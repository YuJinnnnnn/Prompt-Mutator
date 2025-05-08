import random
import spacy
from typing import List, Literal
from nltk.corpus import wordnet as wn
import difflib
from markupsafe import Markup

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

ChangeLevel = Literal["minor", "moderate", "dramatic", "random"]
TARGET_DEP_LABELS = {"nsubj", "dobj", "pobj", "attr"}

def get_wordnet_replacement(word: str, level: ChangeLevel) -> str:
    synsets = wn.synsets(word, pos=wn.NOUN)
    word_lower = word.lower()

    # MINOR LEVEL: Broad synonym selection across all synsets
    if level == "minor":
        synonyms = set()
        for syn in synsets:
            for lemma in syn.lemmas():
                name = lemma.name().replace("_", " ")
                if name.lower() != word_lower:
                    synonyms.add(name)
        if synonyms:
            return random.choice(list(synonyms))
        else:
            # Force artificial minor variation if no real synonyms
            return word + random.choice(["*", "~", "^", "'"])

    # MODERATE LEVEL: hyponyms or hypernyms
    elif level == "moderate":
        hypos = synsets[0].hyponyms() if synsets else []
        hypers = synsets[0].hypernyms() if synsets else []
        candidates = hypos + hypers
        if candidates:
            random_synset = random.choice(candidates)
            lemmas = random_synset.lemmas()
            if lemmas:
                return random.choice(lemmas).name().replace("_", " ")
        return word + random.choice(["#", "@", "&"])

    # DRAMATIC LEVEL: totally random noun from WordNet
    elif level == "dramatic":
        all_nouns = list(wn.all_synsets(wn.NOUN))
        random_synset = random.choice(all_nouns)
        lemmas = random_synset.lemmas()
        if lemmas:
            return random.choice(lemmas).name().replace("_", " ")
        return word + random.choice(["?", "!", "%"])

    # RANDOM LEVEL: Choose a random strategy
    else:
        return get_wordnet_replacement(word, random.choice(["minor", "moderate", "dramatic"]))

def mutate_prompt(prompt: str, level: ChangeLevel = "random") -> str:
    doc = nlp(prompt)
    modified_tokens: List[str] = []

    for token in doc:
        if token.dep_ in TARGET_DEP_LABELS and token.pos_ in {"NOUN", "PROPN"}:
            replacement = get_wordnet_replacement(token.text, level)
            modified_tokens.append(replacement)
        else:
            modified_tokens.append(token.text)

    return ' '.join(modified_tokens)

def mutate_prompt_variants(prompt: str, level: ChangeLevel = "random", n: int = 3) -> List[str]:
    return [mutate_prompt(prompt, level) for _ in range(n)]

def highlight_changes(original, mutated):
    original_words = original.split()
    mutated_words = mutated.split()

    matcher = difflib.SequenceMatcher(None, original_words, mutated_words)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.extend(mutated_words[j1:j2])
        elif tag in ('replace', 'insert'):
            for word in mutated_words[j1:j2]:
                result.append(f"<span class='highlight'>{word}</span>")

    return Markup(" ".join(result))
