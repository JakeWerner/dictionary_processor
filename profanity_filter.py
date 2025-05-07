import argparse
import os

# --- Configuration ---
# Default path for the list of profane words.
# This can be overridden by a command-line argument.
DEFAULT_PROFANITY_LIST_PATH = 'profanity_list.txt'

def load_profane_words(filepath):
    """
    Loads profane words from a given file into a set for efficient lookup.
    Words are expected to be one per line and are converted to lowercase.
    """
    profane_set = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                profane_set.add(line.strip().lower())
        print(f"Successfully loaded {len(profane_set)} profane words from '{filepath}'.")
    except FileNotFoundError:
        print(f"Warning: Profanity list file not found at '{filepath}'. No words will be filtered as profane.")
    except Exception as e:
        print(f"Error loading profane words from '{filepath}': {e}")
    return profane_set

def filter_words(input_filepath, output_filepath, profane_words_set):
    """
    Reads words from the input file, filters out profane words,
    and writes the clean words to the output file.
    """
    words_read = 0
    words_written = 0
    words_filtered = 0

    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile, \
             open(output_filepath, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                words_read += 1
                word = line.strip()
                # Perform case-insensitive check
                if word.lower() in profane_words_set:
                    words_filtered += 1
                    # Optional: print which words are being filtered for debugging
                    # print(f"Filtered profane word: {word}")
                else:
                    outfile.write(word + '\n')
                    words_written += 1
        
        print(f"\nFiltering complete.")
        print(f"Words read from '{input_filepath}': {words_read}")
        print(f"Profane words filtered out: {words_filtered}")
        print(f"Clean words written to '{output_filepath}': {words_written}")

    except FileNotFoundError:
        print(f"Error: Input word list file not found at '{input_filepath}'.")
    except Exception as e:
        print(f"An error occurred during filtering: {e}")

def main():
    """
    Main function to parse arguments and orchestrate the filtering process.
    """
    parser = argparse.ArgumentParser(
        description="Filters a word list to remove profane words.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file",
        help="Path to the input word list file (one word per line)."
    )
    parser.add_argument(
        "output_file",
        help="Path to the output file where the filtered (clean) word list will be saved."
    )
    parser.add_argument(
        "--profanity_list",
        default=DEFAULT_PROFANITY_LIST_PATH,
        help=(
            "Path to the file containing profane words (one word per line).\n"
            f"Defaults to '{DEFAULT_PROFANITY_LIST_PATH}' in the script's directory if not provided."
        )
    )
    # Optional: Add an argument for exact match vs. substring match,
    # but for a word list, exact match is usually what's desired.

    args = parser.parse_args()

    print("--- LexiGlyph Profanity Filter ---")

    # Load the set of profane words
    profane_set = load_profane_words(args.profanity_list)

    # Perform the filtering
    filter_words(args.input_file, args.output_file, profane_set)

if __name__ == "__main__":
    main()
