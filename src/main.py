from src import utils as util
import asyncio 


def main():
    # Load Config, Prompt and Schema
    config = util.get_config()
    prompt = util.get_prompt()
    schema = util.get_schema()


    # Load Client and Generation config 
    client, generation_config = util.get_client(config, prompt, schema)

    # Load Filenames 
    filenames = util.get_filenames(config)

    # Load Semaphore
    semaphore = util.get_semaphore(config)

    # Run Inference
    args = [filenames, semaphore, config , prompt, client, generation_config]
    asyncio.run(util.run_inference(*args))
    

if __name__ == "__main__":
    main()