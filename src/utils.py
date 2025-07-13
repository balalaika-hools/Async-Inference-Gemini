import yaml
from typing import Dict, Any
from google import genai
from google.genai import types
from google.genai.types import Part
import os
from tqdm.asyncio import tqdm
import json
import pandas as pd
import random
import asyncio
from tenacity import retry, wait_random_exponential, stop_after_attempt


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(THIS_DIR)


def load_config(config_path) -> Dict[str, Any]:
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)  # Load YAML as a Python dictionary
        return config
    except FileNotFoundError:
        print(f"❌ Error: The file '{config_path}' was not found.")
        raise
    except yaml.YAMLError as e:
        print(f"❌ Error: Failed to parse YAML file '{config_path}'.\nDetails: {e}")
        raise
    except Exception as e:
        print(f"❌ An error occurred while reading '{config_path}': {e}")
        raise


def get_config():
    return load_config(os.path.join(PROJECT_DIR, "config/config.yaml"))


def get_prompt():
    return load_config(os.path.join(PROJECT_DIR, "misc/prompts/prompt.yaml"))


def get_schema():
    schema_path = os.path.join(PROJECT_DIR, "misc", "schemas", "schema.json")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"❌ Schema file not found at: {schema_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in schema file: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error while loading schema: {e}")
        raise
    return schema


def get_client(config, prompt, schema):
    # Init Vertex-AI Client and Config File
    client = genai.Client(
        vertexai=True, project=config.get("PROJECT_ID"), location=config.get("LOCATION")
    )

    generation_config = types.GenerateContentConfig(
        system_instruction=prompt["SYSTEM"],
        temperature=config.get("TEMPERATURE"),
        top_p=config.get("TOP_P"),
        top_k=config.get("TOP_K"),
        candidate_count=config.get("CANDIDATE_COUNT"),
        max_output_tokens=config.get("MAX_OUTPUT_TOKENS"),
        presence_penalty=config.get("PRESENCE_PENALTY"),
        frequency_penalty=config.get("FREQUENCY_PENALTY"),
        response_mime_type="application/json",
        response_schema=schema,
        seed=config.get("SEED"),
        labels=config.get("LABELS"),
        thinking_config=types.ThinkingConfig(
            thinking_budget=config.get("THINKING_BUDGET")
        ),
    )
    return client, generation_config


def get_filenames(config):
    filenames = os.listdir(config.get("PDF_FOLDER_PATH"))
    # Sample a few files
    if config.get("SAMPLE") is not None:
        filenames = random.sample(filenames, config["SAMPLE"])
    return filenames


def get_semaphore(config):
    return asyncio.Semaphore(config.get("CONC_TASKS"))


def get_generate_with_retry(client, config, generation_config):
    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(config.get("MAX_RETRIES")),
        reraise=True,
    )
    async def inner(contents):
        return await client.aio.models.generate_content(
            model=config["MODEL"], contents=contents, config=generation_config
        )

    return inner


async def process_file(filename, semaphore, config, prompt, client, generation_config):
    async with semaphore:
        filepath = os.path.join(config["PDF_FOLDER_PATH"], filename)

        try:
            with open(filepath, "rb") as file:
                file_bytes = file.read()
            mime_type = get_mime_type(filepath)
            pdf_part = Part.from_bytes(data=file_bytes, mime_type=mime_type)
            contents = [pdf_part, prompt["USER"]]

            generate_with_retry = get_generate_with_retry(
                client, config, generation_config
            )
            response = await generate_with_retry(contents)
            result_text = json.loads(response.text)

            return {"filepath": filename, "response": result_text, "success": True}

        except Exception as e:
            return {"filepath": filename, "error": str(e), "success": False}


async def run_inference(
    filenames, semaphore, config, prompt, client, generation_config
):
    results = []
    failed = []
    failed_count = 0

    tasks = [
        process_file(fname, semaphore, config, prompt, client, generation_config)
        for fname in filenames
    ]

    for future in tqdm(
        asyncio.as_completed(tasks),
        total=len(tasks),
        desc="Processing files",
        colour="green",
    ):
        result = await future

        if result.get("success"):
            # Keep only what you need for output
            results.append(
                {"filepath": result["filepath"], "response": result["response"]}
            )
        else:
            failed_count += 1
            failed.append({"filepath": result["filepath"], "error": result["error"]})

        # Graceful early termination if too many failed
        if failed_count >= config.get("MAX_FAILED"):
            print(f"\n❌ Too many failed requests ({failed_count}). Aborting...")
            break

    # Save successful results
    with open(
        os.path.join(PROJECT_DIR, "misc/output/results.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save failed requests
    with open(
        os.path.join(PROJECT_DIR, "misc/output/failed_requests.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done: {len(results)} succeeded, {len(failed)} failed.")



def get_mime_type(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".pdf":
        mime_type = "application/pdf"
    elif ext == ".png":
        mime_type = "image/png"
    elif ext in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    else:
        mime_type = None
    return mime_type