import json
from collections import Counter
from itertools import combinations

# --- CONFIGURATION ---
# These are the values you'll need to tune extensively.
# Consider moving these to a separate config file (e.g., config.json or config.py) for larger projects.

# I. File Paths
RAW_WORD_LIST_PATH = 'raw_word_list.txt'  # Your input file
OUTPUT_JSON_PATH = 'lexiglyph_dictionary.json' # Your output file

# II. Word Validation Parameters
MIN_WORD_LENGTH = 3
MAX_WORD_LENGTH = 10 # Adjust as needed for your game

# III. Scoring Weights
LENGTH_WEIGHT = 1.0 # Score per letter
RARITY_WEIGHT = 1.5 # Multiplier for summed letter rarity scores
REPEATED_INSTANCE_PENALTY = 5.0 # Penalty for each extra instance of a repeated letter
VISUAL_CONFUSION_WEIGHT = 10.0 # Multiplier for summed pair confusion scores

# IV. Letter Rarity Scores
# Assign a score to each letter. Higher = rarer/harder.
# This is an example; you'll want to create a more comprehensive list.
# Based on typical English letter frequencies (lower score = more frequent)
LETTER_RARITY_SCORES = {
    'A': 1, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 3, 'H': 2, 'I': 1,
    'J': 8, 'K': 5, 'L': 2, 'M': 3, 'N': 2, 'O': 1, 'P': 3, 'Q': 9, 'R': 1,
    'S': 1, 'T': 1, 'U': 2, 'V': 5, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10
}

# V. Pair Confusion Scores (Font-Specific - e.g., for Roboto Light)
# Score for how visually confusing specific pairs of letters are when overlaid.
# Keys should be tuples of letters, sorted alphabetically to ensure consistency.
# This table will require significant manual effort and visual assessment.
# Example: ('LETTER1', 'LETTER2'): score
PAIR_CONFUSION_SCORES = {
    ('E', 'F'): 3,  # E and F might look similar when overlaid
    ('I', 'L'): 2,
    ('O', 'Q'): 4,
    ('P', 'R'): 3,
    ('C', 'G'): 2,
    ('M', 'N'): 1, # Less confusing
    ('V', 'W'): 2,
    # Add many more pairs based on your visual assessment of Roboto Light
}

# VI. Difficulty Category Score Ranges
# The upper bound of the previous category is the lower bound of the next (exclusive for min, inclusive for max).
DIFFICULTY_CATEGORIES_CONFIG = {
    # CategoryName: (min_score, max_score)
    "Easy": (0, 70),
    "Medium": (71, 150),
    "Hard": (151, float('inf')) # float('inf') means no upper limit for the hardest category
}
# --- END CONFIGURATION ---

def clean_and_validate_word(word_text):
    """
    Cleans and validates a single word.
    Returns the cleaned word in uppercase or None if invalid.
    """
    cleaned = word_text.strip().upper()
    if not cleaned.isalpha():
        # print(f"Skipping non-alphabetic word: {word_text}")
        return None
    if not (MIN_WORD_LENGTH <= len(cleaned) <= MAX_WORD_LENGTH):
        # print(f"Skipping word due to length: {cleaned} (Length: {len(cleaned)})")
        return None
    # Future: Add profanity filter if needed
    return cleaned

def calculate_difficulty_score(word):
    """
    Calculates the numerical difficulty score for a single word.
    """
    score = 0.0

    # 1. Length Score
    score += LENGTH_WEIGHT * len(word)

    # 2. Rarity Score
    total_rarity_score_for_word = 0
    for letter in word:
        total_rarity_score_for_word += LETTER_RARITY_SCORES.get(letter, 0) # Default to 0 if letter somehow not in scores
    score += RARITY_WEIGHT * total_rarity_score_for_word

    # 3. Repeated Instance Score
    letter_counts = Counter(word)
    total_extra_instances = 0
    for letter in letter_counts:
        if letter_counts[letter] > 1:
            total_extra_instances += (letter_counts[letter] - 1)
    score += REPEATED_INSTANCE_PENALTY * total_extra_instances

    # 4. Visual Confusion Score
    unique_letters_in_word = sorted(list(set(word))) # Sorted for consistent pair generation
    total_pair_confusion_score = 0
    if len(unique_letters_in_word) >= 2:
        for pair in combinations(unique_letters_in_word, 2):
            # Ensure pair is always in ('L1', 'L2') where L1 < L2 for PAIR_CONFUSION_SCORES lookup
            # (combinations already produces sorted tuples if the input is sorted)
            total_pair_confusion_score += PAIR_CONFUSION_SCORES.get(pair, 0)
    score += VISUAL_CONFUSION_WEIGHT * total_pair_confusion_score
    
    return score

def get_difficulty_category(score):
    """
    Determines the difficulty category string based on the score.
    """
    for category_name, (min_score, max_score) in DIFFICULTY_CATEGORIES_CONFIG.items():
        if min_score <= score <= max_score:
            return category_name
    return "Unknown" # Should not happen if ranges are set up correctly

def preprocess_dictionary():
    """
    Main function to load, process, and save the dictionary.
    """
    print("Starting LexiGlyph dictionary preprocessing...")
    processed_words_data = []
    words_by_category = {category_name: [] for category_name in DIFFICULTY_CATEGORIES_CONFIG.keys()}
    words_by_category["Unknown"] = [] # For any words that might fall out of defined ranges

    try:
        with open(RAW_WORD_LIST_PATH, 'r', encoding='utf-8') as f:
            raw_words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"ERROR: Raw word list file not found at '{RAW_WORD_LIST_PATH}'")
        return
    except Exception as e:
        print(f"ERROR: Could not read raw word list: {e}")
        return

    print(f"Loaded {len(raw_words)} words from '{RAW_WORD_LIST_PATH}'.")

    valid_word_count = 0
    for raw_word in raw_words:
        word = clean_and_validate_word(raw_word)
        if not word:
            continue
        
        valid_word_count +=1
        difficulty_score = calculate_difficulty_score(word)
        category = get_difficulty_category(difficulty_score)
        
        # Output structure: { "word": "FLUTTER", "category": "Medium", "score": 123.5 }
        # You can decide if you want the score in the final JSON for the game.
        # For the game, only "word" and "category" might be needed.
        word_entry = {"word": word, "category": category, "score": round(difficulty_score, 2)}
        processed_words_data.append(word_entry)
        
        words_by_category[category].append(word_entry)


    # Sorting within categories, e.g., by word or score, is optional
    # for word_list in words_by_category.values():
    #     word_list.sort(key=lambda x: x['score'])


    # Outputting a structure that groups words by category might be more useful for the game
    # Example: { "Easy": [{"word": "CAT", ...}, ...], "Medium": [...] }
    output_structure = {}
    for category_name, entries in words_by_category.items():
        # Storing only the word if category is sufficient, or full entry if score is also useful
        output_structure[category_name] = [{"word": entry["word"], "score": entry["score"]} for entry in entries]
        # If you only need the word in the game:
        # output_structure[category_name] = [entry["word"] for entry in entries]


    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f_out:
            json.dump(output_structure, f_out, indent=4) # indent for pretty printing
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
