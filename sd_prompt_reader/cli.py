__author__ = "receyuki"
__filename__ = "cli.py"
__copyright__ = "Copyright 2024"
__email__ = "receyuki@gmail.com"

import json
from pathlib import Path

import click
from .image_data_reader import ImageDataReader
from .constants import SUPPORTED_FORMATS
from .logger import Logger


@click.command()
# Feature mode
@click.option(
    "-r", "--read", "operation", flag_value="read", help="Read mode", default=True
)
@click.option("-w", "--write", "operation", flag_value="write", help="Write mode")
@click.option("-c", "--clear", "operation", flag_value="clear", help="Clear mode")
# Option
@click.option("-i", "--input-path", type=str, help="Input path", required=True)
@click.option("-o", "--output-path", type=str, help="Output path")
@click.option(
    "-f",
    "--format-type",
    default="TXT",
    type=click.Choice(["TXT", "JSON"], case_sensitive=False),
)
@click.option("-m", "--metadata", type=str, help="Metadata file")
@click.option("-p", "--positive", type=str, help="Positive prompt")
@click.option("-n", "--negative", type=str, help="Negative prompt")
@click.option("-s", "--setting", type=str, help="Setting")
@click.option(
    "-l",
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR"], case_sensitive=False),
)
def cli(
    operation,
    input_path,
    output_path,
    metadata,
    positive,
    negative,
    setting,
    format_type,
    log_level,
):

    logger = Logger("SD_Prompt_Reader.Cli")
    Logger.configure_global_logger(log_level)

    # Ensure the input path exists
    source = Path(input_path)
    logger.debug(f"Input: {source}")
    if not source.exists():
        logger.error("Input doesn't exist")
        raise click.UsageError("The specified input path does not exist.")
    elif source.is_file():
        logger.debug("Input is a file")
        file_list = [input_path]
    else:
        logger.debug("Input is a folder")
        file_list = [
            file
            for file in source.glob("*")
            if file.is_file() and file.suffix in SUPPORTED_FORMATS
        ]
        logger.debug(f"Total file detected: {len(file_list)}")

    match operation:
        case "read":
            logger.debug("Read mode")
            success_count = 0
            read_list = {}
            failure_list = {}
            for file in file_list:
                logger.debug(f"Reading file: {file}")
                with open(file, "rb") as f:
                    image_data = ImageDataReader(f)
                    if image_data.status.name == "READ_SUCCESS":
                        logger.debug("Read successfully")
                        success_count += 1
                        if source.is_file():
                            click.echo(image_data.raw)
                        read_list[file] = image_data
                    else:
                        logger.warning(
                            f"Unable to read {file} due to {image_data.status.name}"
                        )
                        failure_list[file] = image_data.status.name
            if source.is_dir():
                logger.info(f"Total files read: {len(file_list)}")
                logger.info(f"Successful: {success_count}")
                if failure_list:
                    logger.info("List of failed files:")
                    for file, status in failure_list.items():
                        logger.info(f"{file}: {status}")

            if output_path:
                target = Path(output_path)
                logger.debug(f"Output: {target}")
                for file, image_data in read_list.items():
                    logger.debug(f"Exporting file: {file}")
                    file_path = Path(file)
                    if target.is_dir():
                        logger.debug("Output folder exists")
                        folder = target
                        stem = file_path.stem
                    elif target.is_file():
                        if source.is_dir():
                            logger.error("Output is a file not a folder")
                            raise click.UsageError(
                                "If input path is a directory, the output path must be a directory, not a file."
                            )
                        logger.debug("Output file exists, overwrite the old file.")
                        folder = target.parent
                        stem = target.stem
                        if not format_type:
                            format_type = target.suffix.strip(".")
                    else:
                        if target.suffix:
                            if source.is_dir():
                                logger.error("Output is a file not a folder")
                                raise click.UsageError(
                                    "If input path is a directory, the output path must be a directory, not a file."
                                )
                            logger.debug("Output file doesn't exist")
                            logger.debug("Creating a new file")
                            folder = target.parent
                            stem = target.stem
                            if not format_type:
                                format_type = target.suffix.strip(".")
                        else:
                            logger.debug("Output folder doesn't exist")
                            logger.debug("Creating a new folder")
                            folder = target
                            stem = file_path.stem
                        folder.mkdir(parents=True, exist_ok=True)
                    target_file_name = folder / stem
                    try:
                        match format_type:
                            case "TXT":
                                logger.debug("Output format: TXT")
                                with open(
                                    target_file_name.with_suffix(".txt"),
                                    "w",
                                    encoding="utf-8",
                                ) as f:
                                    f.write(image_data.raw)
                                    logger.debug("Output successful")
                            case "JSON":
                                logger.debug("Output format: JSON")
                                with open(
                                    target_file_name.with_suffix(".json"),
                                    "w",
                                    encoding="utf-8",
                                ) as f:
                                    parameter = {
                                        "positive": image_data.positive,
                                        "negative": image_data.negative,
                                        "setting": image_data.setting,
                                    }
                                    parameter.update(image_data.parameter)
                                    json.dump(parameter, f, indent=4)
                                    logger.debug("Output successful")
                            case _:
                                logger.error(
                                    f"{format_type} is not one of 'TXT', 'JSON'"
                                )
                    except IOError as e:
                        logger.error(f"File save failed: {e}")

        case "write" | "clear":
            if operation == "write":
                logger.debug("Write mode")
                if source.is_dir():
                    logger.error("Input is a folder not a file")
                    raise click.UsageError(
                        "In write mode, the input path must be a file, not a directory."
                    )
                if metadata:
                    logger.debug("Metadata file is specified")
                    metadata_path = Path(metadata)
                    with open(metadata_path, "rb") as f:
                        if metadata_path.suffix.lower() == ".txt":
                            data = f.read()
                        elif metadata_path.suffix.lower() == ".json":
                            data_dict = json.load(f)
                            data = ImageDataReader.construct_data(
                                data_dict.get("positive"),
                                data_dict.get("negative"),
                                data_dict.get("setting"),
                            )
                        else:
                            data = ""
                        click.echo(data)
                elif positive or negative or setting:
                    logger.debug("Metadata text is specified")
                    data = ImageDataReader.construct_data(positive, negative, setting)
                    click.echo(data)
            if operation == "clear":
                logger.debug("Clear mode")
            success_count = 0
            if output_path:
                target = Path(output_path)
                logger.debug(f"Output: {target}")
                for file in file_list:
                    logger.debug(f"Processing file: {file}")
                    file_path = Path(file)
                    if target.is_dir():
                        logger.debug("Output folder exists")
                        folder = target
                        stem = file_path.stem
                    elif target.is_file():
                        if source.is_dir():
                            logger.error("Output is a file not a folder")
                            raise click.UsageError(
                                "If input path is a directory, the output path must be a directory, not a file."
                            )
                        logger.debug("Output file exists, overwrite the old file.")
                        folder = target.parent
                        stem = target.stem
                    else:
                        if target.suffix:
                            if source.is_dir():
                                logger.error("Output is a file not a folder")
                                raise click.UsageError(
                                    "If input path is a directory, the output path must be a directory, not a file."
                                )
                            logger.debug("Output file doesn't exist")
                            logger.debug("Creating a new file")
                            folder = target.parent
                            stem = target.stem
                        else:
                            logger.debug("Output folder doesn't exist")
                            logger.debug("Creating a new folder")
                            folder = target
                            stem = file_path.stem
                        folder.mkdir(parents=True, exist_ok=True)
                    target_file_name = folder / stem
                    try:
                        ImageDataReader.save_image(
                            file,
                            target_file_name.with_suffix(file_path.suffix),
                            file_path.suffix.lstrip(".").upper(),
                            None if operation == "clear" else data,
                        )
                    except IOError as e:
                        logger.error(f"File save failed: {e}")
                    else:
                        logger.debug("Output successful")
                        success_count += 1
            else:
                logger.debug("Output not specified, output to original location")
                for file in file_list:
                    file_path = Path(file)
                    folder = file_path.parent
                    stem = (
                        f"{file_path.stem}_data_removed{file_path.suffix}"
                        if operation == "clear"
                        else f"{file_path.stem}_edited{file_path.suffix}"
                    )
                    target_file_name = folder / stem
                    try:
                        ImageDataReader.save_image(
                            file,
                            target_file_name,
                            file_path.suffix.lstrip(".").upper(),
                            None if operation == "clear" else data,
                        )
                    except IOError as e:
                        logger.error(f"File save failed: {e}")
                    else:
                        logger.debug("Output successful")
                        success_count += 1

            if len(file_list) > 1:
                logger.info(f"Total files processed: {len(file_list)}")
                logger.info(f"Successful: {success_count}")


if __name__ == "__main__":
    cli()
