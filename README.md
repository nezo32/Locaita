# LocAIta

LocAIta is an advanced AI-powered project with various usage directions

## Project structure

```
.
├── external/           # External dependencies and submodules
│   └── osu_game/       # osu! game source code modified for RL training
├── legacy/             # Legacy code and tools
├── logs/               # Log files
└── src/                # Source code
    ├── locaita/        # Main project folder
    │   └── modules/    # Project modules
    │       └── osu/    # osu! RL module
    ├── log/            # Logging utilities
    ├── scripts/        # Scripts (entrypoints)
    └── utils/          # Common utilities
```

## Setting up

Please make sure you have the following prerequisites:

- A desktop platform with the [.NET 8.0 SDK](https://dotnet.microsoft.com/download) installed.
- Installed python >= 3.13

### Getting started

1. Clone the repository:

```sh
$ git clone https://github.com/nezo32/Locaita.git
$ cd Locaita
```

2. Fetch/Update submodules:

```sh
$ git submodule update --init --recursive --remote
```

3. Install `uv` [here](https://docs.astral.sh/uv/getting-started/installation/)

4. Install dependencies

```sh
$ uv sync
```

## Usage

#### RL osu! module

1. Start osu! game

```
$ uv run osu
```

2. Wait for osu! to open

3. Start `osu-train` script

```
$ uv run osu-train
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
