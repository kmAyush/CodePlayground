from backend.sandbox import run_in_sandbox
from core.main import run_hindi_source, translate_source

with open("inputs/error.py", "r", encoding="utf-8") as file:
    english_source = file.read()

hindi_source, reverse_map = translate_source(english_source)

print("=== Hindi Source ===")
print(hindi_source)

english_output, english_error = run_in_sandbox(english_source)
hindi_output, hindi_error = run_hindi_source(hindi_source, reverse_map)

print("\n=== English Output ===")
print(english_output, end="")
if english_error:
    print("--- English Error ---")
    print(english_error, end="")

print("\n=== Hindi Output ===")
print(hindi_output, end="")
if hindi_error:
    print("--- Hindi Error ---")
    print(hindi_error)

