from core.generator import export_json, generate_games, load_config


if __name__ == "__main__":
    config = load_config()
    export_json(generate_games(config=config), config=config)
