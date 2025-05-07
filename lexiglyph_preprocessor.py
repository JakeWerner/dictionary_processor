import json
from collections import Counter
from itertools import combinations
import os # Added for path joining

# --- CONFIGURATION ---
# I. File Paths
RAW_WORD_LIST_PATH = 'raw_word_list.txt'
OUTPUT_JSON_PATH = 'lexiglyph_dictionary.json'
# New path for pair confusion scores:
PAIR_CONFUSION_SCORES_PATH = 'pair_confusion_scores.json'

# II. Word Validation Parameters
MIN_WORD_LENGTH = 3
MAX_WORD_LENGTH = 10

# III. Scoring Weights
LENGTH_WEIGHT = 1.0
RARITY_WEIGHT = 1.5
REPEATED_INSTANCE_PENALTY = 5.0
VISUAL_CONFUSION_WEIGHT = 10.0 # This weight is now more critical

# IV. Letter Rarity Scores (keep as is, or also move to JSON if preferred)
LETTER_RARITY_SCORES = {
    'A': 1, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 3, 'H': 2, 'I': 1,
    'J': 8, 'K': 5, 'L': 2, 'M': 3, 'N': 2, 'O': 1, 'P': 3, 'Q': 9, 'R': 1,
    'S': 1, 'T': 1, 'U': 2, 'V': 5, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10
}

# V. Pair Confusion Scores will be loaded from the JSON file
# The PAIR_CONFUSION_SCORES variable will be populated by load_pair_confusion_scores()
PAIR_CONFUSION_SCORES = {} # Initialize as empty

# VI. Difficulty Category Score Ranges
DIFFICULTY_CATEGORIES_CONFIG = {
    "Easy": (0, 70),
    "Medium": (71, 150),
    "Hard": (151, float('inf'))
}
# --- END CONFIGURATION ---

def load_pair_confusion_scores(filepath):
    """
    Loads pair confusion scores from a JSON file.
    Converts string keys "L1_L2" to tuple keys ('L1', 'L2').
    """
    loaded_scores = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for key, score in data.items():
                parts = key.split('_')
                if len(parts) == 2:
                    # Ensure tuple is sorted alphabetically, matching generation logic
                    pair_tuple = tuple(sorted((parts[0].upper(), parts[1].upper())))
                    loaded_scores[pair_tuple] = score
                else:
                    print(f"Warning: Invalid key format in '{filepath}': {key}")
            print(f"Successfully loaded {len(loaded_scores)} pair confusion scores from '{filepath}'.")
            return loaded_scores
    except FileNotFoundError:
        print(f"ERROR: Pair confusion scores file not found at '{filepath}'. Defaulting to empty scores.")
        return {}
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from '{filepath}'. Defaulting to empty scores.")
        return {}
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading pair confusion scores: {e}. Defaulting to empty scores.")
        return {}

def clean_and_validate_word(word_text):
    """
    Cleans and validates a single word.
    Returns the cleaned word in uppercase or None if invalid.
    """
    cleaned = word_text.strip().upper()
    if not cleaned.isalpha():
        return None
    if not (MIN_WORD_LENGTH <= len(cleaned) <= MAX_WORD_LENGTH):
        return None
    return cleaned

def calculate_difficulty_score(word, current_pair_confusion_scores): # Now takes scores as arg
    """
    Calculates the numerical difficulty score for a single word.
    """
    score = 0.0

    # 1. Length Score
    score += LENGTH_WEIGHT * len(word)

    # 2. Rarity Score
    total_rarity_score_for_word = 0
    for letter in word:
        total_rarity_score_for_word += LETTER_RARITY_SCORES.get(letter, 0)
    score += RARITY_WEIGHT * total_rarity_score_for_word

    # 3. Repeated Instance Score
    letter_counts = Counter(word)
    total_extra_instances = 0
    for letter_count in letter_counts.values(): # Iterate through counts directly
        if letter_count > 1:
            total_extra_instances += (letter_count - 1)
    score += REPEATED_INSTANCE_PENALTY * total_extra_instances

    # 4. Visual Confusion Score
    unique_letters_in_word = sorted(list(set(word)))
    total_pair_confusion_score = 0
    if len(unique_letters_in_word) >= 2:
        for pair_tuple in combinations(unique_letters_in_word, 2):
            # The pair_tuple from combinations will already be sorted if unique_letters_in_word is sorted
            total_pair_confusion_score += current_pair_confusion_scores.get(pair_tuple, 0) # Use passed scores
    score += VISUAL_CONFUSION_WEIGHT * total_pair_confusion_score
    
    return score

def get_difficulty_category(score):
    """
    Determines the difficulty category string based on the score.
    """
    for category_name, (min_score, max_score) in DIFFICULTY_CATEGORIES_CONFIG.items():
        if min_score <= score <= max_score:
            return category_name
    # If score is higher than any max_score (e.g. if Hard category was not float('inf'))
    # or if no category matches (shouldn't happen with float('inf'))
    # Fallback, or adjust categories
    if score > DIFFICULTY_CATEGORIES_CONFIG.get("Hard", (0, float('inf')))[1] and "Hard" in DIFFICULTY_CATEGORIES_CONFIG:
        return "Hard" # Should be caught by Hard's inf range
    return "Unknown"


def preprocess_dictionary():
    """
    Main function to load, process, and save the dictionary.
    """
    global PAIR_CONFUSION_SCORES # To update the global variable
    
    print("Starting LexiGlyph dictionary preprocessing...")
    
    # Load pair confusion scores from JSON file
    PAIR_CONFUSION_SCORES = load_pair_confusion_scores(PAIR_CONFUSION_SCORES_PATH)
    if not PAIR_CONFUSION_SCORES:
        print("Warning: Proceeding with no or incomplete pair confusion scores. Visual confusion component might be ineffective.")

    processed_words_data = []
    # Initialize words_by_category ensuring all defined categories exist
    words_by_category = {category_name: [] for category_name in DIFFICULTY_CATEGORIES_CONFIG.keys()}
    if "Unknown" not in words_by_category: # Ensure Unknown category exists for uncategorized words
         words_by_category["Unknown"] = []


    try:
        with open(RAW_WORD_LIST_PATH, 'r', encoding='utf-8') as f:
            raw_words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"ERROR: Raw word list file not found at '{RAW_WORD_LIST_PATH}'")
        return
    except Exception as e:
        print(f"ERROR: Could not read raw word list: {e}")
        return

    print(f"Loaded {len(raw_words)} raw words from '{RAW_WORD_LIST_PATH}'.")

    valid_word_count = 0
    for raw_word in raw_words:
        word = clean_and_validate_word(raw_word)
        if not word:
            continue
        
        valid_word_count +=1
        # Pass the loaded PAIR_CONFUSION_SCORES to the calculation function
        difficulty_score = calculate_difficulty_score(word, PAIR_CONFUSION_SCORES)
        category = get_difficulty_category(difficulty_score)
        
        word_entry = {"word": word, "category": category, "score": round(difficulty_score, 2)}
        # Append to the main list (optional, if you only want the categorized structure)
        # processed_words_data.append(word_entry) 
        
        # Append to the correct category list
        if category in words_by_category:
            words_by_category[category].append(word_entry)
        else: # Should ideally not happen if get_difficulty_category works correctly
            words_by_category["Unknown"].append(word_entry)


    output_structure = {}
    for category_name, entries in words_by_category.items():
        # Sort entries by score within each category
        sorted_entries = sorted(entries, key=lambda x: x['score'])
        output_structure[category_name] = [{"word": entry["word"], "score": entry["score"]} for entry in sorted_entries]

    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f_out:
            json.dump(output_structure, f_out, indent=4)
        print(f"\nSuccessfully processed {valid_word_count} valid words.")
        print(f"Categorized dictionary saved to '{OUTPUT_JSON_PATH}'.")
    except Exception as e:
        print(f"ERROR: Could not save processed dictionary: {e}")
        return

    print("\n--- Category Distribution ---")
    for category_name, word_list in output_structure.items():
        print(f"{category_name}: {len(word_list)} words")

if __name__ == "__main__":
    preprocess_dictionary()
