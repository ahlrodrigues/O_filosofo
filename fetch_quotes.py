#!/usr/bin/env python3
import os
import json
import uuid
import requests

OUTPUT_FILE = os.getenv("OUTPUT_FILE", "quotes_new.json")
TARGET_COUNT = int(os.getenv("TARGET_COUNT", "50").strip() or "50")


PHILOSOPHICAL_QUOTES = [
    {"quote": "You have power over your mind, not outside events.", "author": "Marcus Aurelius", "theme": "self-control"},
    {"quote": "The happiness of your life depends upon the quality of your thoughts.", "author": "Marcus Aurelius", "theme": "thought"},
    {"quote": "The soul becomes dyed with the color of its thoughts.", "author": "Marcus Aurelius", "theme": "inner-life"},
    {"quote": "The best revenge is not to be like your enemy.", "author": "Marcus Aurelius", "theme": "ethics"},
    {"quote": "Confine yourself to the present.", "author": "Marcus Aurelius", "theme": "presence"},
    {"quote": "It is not death that a man should fear, but he should fear never beginning to live.", "author": "Marcus Aurelius", "theme": "life"},
    {"quote": "Very little is needed to make a happy life; it is all within yourself.", "author": "Marcus Aurelius", "theme": "happiness"},
    {"quote": "When you arise in the morning, think of what a privilege it is to be alive.", "author": "Marcus Aurelius", "theme": "gratitude"},
    {"quote": "The objective of life is not to achieve wealth but to achieve inner peace.", "author": "Marcus Aurelius", "theme": "wisdom"},
    {"quote": "Accept the things to which fate binds you.", "author": "Marcus Aurelius", "theme": "acceptance"},
    
    {"quote": "We suffer more often in imagination than in reality.", "author": "Seneca", "theme": "fear"},
    {"quote": "It is not that we have a short time to live, but that we waste a lot of it.", "author": "Seneca", "theme": "time"},
    {"quote": "Luck is what happens when preparation meets opportunity.", "author": "Seneca", "theme": "opportunity"},
    {"quote": "He who is brave is free.", "author": "Seneca", "theme": "freedom"},
    {"quote": "Difficulties strengthen the mind, as labor does the body.", "author": "Seneca", "theme": "resilience"},
    {"quote": "As is a tale, so is life: how long it is depends on the teller.", "author": "Seneca", "theme": "life"},
    {"quote": "The greatest remedy for anger is distance.", "author": "Seneca", "theme": "anger"},
    {"quote": "If a man knows not to which port he is sailing, no wind is favorable.", "author": "Seneca", "theme": "purpose"},
    {"quote": "No man is free who is not master of himself.", "author": "Epictetus", "theme": "freedom"},
    {"quote": "It's not what happens to you, but how you react to it that matters.", "author": "Epictetus", "theme": "reaction"},
    
    {"quote": "First, say to yourself what you would be; and then do what you have to do.", "author": "Epictetus", "theme": "action"},
    {"quote": "Man is not worried by real problems so much as by his imagined anxieties.", "author": "Epictetus", "theme": "anxiety"},
    {"quote": "Don't explain your philosophy. Embody it.", "author": "Epictetus", "theme": "philosophy"},
    {"quote": "Wealth consists not in having great possessions, but in having few wants.", "author": "Epictetus", "theme": "simplicity"},
    {"quote": "The key is to keep company only with people who uplift you.", "author": "Epictetus", "theme": "relationships"},
    
    {"quote": "One cannot step twice in the same river.", "author": "Heraclitus", "theme": "change"},
    {"quote": "Character is destiny.", "author": "Heraclitus", "theme": "fate"},
    {"quote": "No man ever steps in the same river twice.", "author": "Heraclitus", "theme": "impermanence"},
    
    {"quote": "The unexamined life is not worth living.", "author": "Socrates", "theme": "self-knowledge"},
    {"quote": "I know that I know nothing.", "author": "Socrates", "theme": "wisdom"},
    {"quote": "The secret of change is to focus all of your energy not on fighting the old, but on building the new.", "author": "Socrates", "theme": "change"},
    {"quote": "Be kind, for everyone you meet is fighting a hard battle.", "author": "Socrates", "theme": "compassion"},
    {"quote": "Strong minds discuss ideas, average minds discuss events, weak minds discuss people.", "author": "Socrates", "theme": "mind"},
    
    {"quote": "One should eat to live, not live to eat.", "author": "Socrates", "theme": "moderation"},
    {"quote": "Education is the kindling of a flame, not the filling of a vessel.", "author": "Socrates", "theme": "education"},
    {"quote": "There is only one good, knowledge, and one evil, ignorance.", "author": "Socrates", "theme": "knowledge"},
    
    {"quote": "The mind is everything. What you think you become.", "author": "Buddha", "theme": "mindfulness"},
    {"quote": "Peace comes from within. Do not seek it without.", "author": "Buddha", "theme": "peace"},
    {"quote": "You will not be punished for your anger, you will be punished by your anger.", "author": "Buddha", "theme": "anger"},
    {"quote": "Three things cannot be long hidden: the sun, the moon, and the truth.", "author": "Buddha", "theme": "truth"},
    {"quote": "In the end, only three things matter: how much you loved, how gently you lived, how gracefully you let go.", "author": "Buddha", "theme": "life"},
    
    {"quote": "Do not dwell in the past, do not dream of the future, concentrate the mind on the present moment.", "author": "Buddha", "theme": "presence"},
    {"quote": "Health is the greatest gift, contentment the greatest wealth, faithfulness the best relationship.", "author": "Buddha", "theme": "values"},
    
    {"quote": "He who has a why to live can bear almost any how.", "author": "Friedrich Nietzsche", "theme": "purpose"},
    {"quote": "That which does not kill us makes us stronger.", "author": "Friedrich Nietzsche", "theme": "strength"},
    {"quote": "Without music, life would be a mistake.", "author": "Friedrich Nietzsche", "theme": "art"},
    {"quote": "The man who moves a mountain begins by carrying away small stones.", "author": "Friedrich Nietzsche", "theme": "perseverance"},
    {"quote": "There are no facts, only interpretations.", "author": "Friedrich Nietzsche", "theme": "truth"},
    
    {"quote": "And those who were seen dancing were thought to be insane by those who could not hear the music.", "author": "Friedrich Nietzsche", "theme": "perception"},
    {"quote": "You must have chaos within you to give birth to a dancing star.", "author": "Friedrich Nietzsche", "theme": "creativity"},
    {"quote": "The snake which cannot cast its skin has to die.", "author": "Friedrich Nietzsche", "theme": "transformation"},
    
    {"quote": "Man is condemned to be free.", "author": "Jean-Paul Sartre", "theme": "freedom"},
    {"quote": "Existence precedes essence.", "author": "Jean-Paul Sartre", "theme": "existence"},
    {"quote": "Hell is other people.", "author": "Jean-Paul Sartre", "theme": "relationships"},
    {"quote": "We are our choices.", "author": "Jean-Paul Sartre", "theme": "choices"},
    {"quote": "Life begins on the other side of despair.", "author": "Jean-Paul Sartre", "theme": "despair"},
    
    {"quote": "Man is not the sum of what he has already, but rather the sum of what he does not yet have.", "author": "Jean-Paul Sartre", "theme": "potential"},
    {"quote": "Every existing thing is born without reason, prolongs itself out of weakness, and dies by chance.", "author": "Jean-Paul Sartre", "theme": "existence"},
    
    {"quote": "One must imagine Sisyphus happy.", "author": "Albert Camus", "theme": "absurdism"},
    {"quote": "In the depth of winter, I finally learned that within me there lay an invincible summer.", "author": "Albert Camus", "theme": "resilience"},
    {"quote": "The absurd is the essential concept and the first truth.", "author": "Albert Camus", "theme": "absurdism"},
    {"quote": "Live to the point of tears.", "author": "Albert Camus", "theme": "life"},
    {"quote": "I rebellion, therefore I am.", "author": "Albert Camus", "theme": "rebellion"},
    
    {"quote": "Life is the sum of all your choices.", "author": "Albert Camus", "theme": "choices"},
    {"quote": "Nobody realizes that some people expend tremendous energy merely to be normal.", "author": "Albert Camus", "theme": "normal"},
    
    {"quote": "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "author": "Ralph Waldo Emerson", "theme": "authenticity"},
    {"quote": "What lies behind us and what lies before us are tiny matters compared to what lies within us.", "author": "Ralph Waldo Emerson", "theme": "inner-strength"},
    {"quote": "Do not go where the path may lead, go instead where there is no path and leave a trail.", "author": "Ralph Waldo Emerson", "theme": "pioneer"},
    {"quote": "The purpose of life is not to be happy. It is to be useful.", "author": "Ralph Waldo Emerson", "theme": "purpose"},
    {"quote": "The only person you are destined to become is the person you decide to be.", "author": "Ralph Waldo Emerson", "theme": "destiny"},
    
    {"quote": "Every secret is a weight. The truth weighs ever so much more.", "author": "Ralph Waldo Emerson", "theme": "truth"},
    {"quote": "Make your own quote. Let others deal with the way they want to.", "author": "Ralph Waldo Emerson", "theme": "independence"},
]


AUTHOR_TRANSlations = {
    "Marcus Aurelius": "Marco Aurélio",
    "Seneca": "Sêneca",
    "Epictetus": "Epicteto",
    "Heraclitus": "Heráclito",
    "Socrates": "Sócrates",
    "Buddha": "Buda",
    "Friedrich Nietzsche": "Friedrich Nietzsche",
    "Jean-Paul Sartre": "Jean-Paul Sartre",
    "Albert Camus": "Albert Camus",
    "Ralph Waldo Emerson": "Ralph Waldo Emerson",
}


def translate_text(text: str, source_lang: str = "en", target_lang: str = "pt") -> str:
    if not text:
        return ""
    
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text[:500], "langpair": f"{source_lang}|{target_lang}"}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("responseStatus") == 200:
                return data.get("responseData", {}).get("translatedText", text)
    except Exception:
        pass
    return f"[PT] {text}"


def generate_quote_id() -> str:
    return f"api{uuid.uuid4().hex[:4]}"


def main():
    import random
    random.shuffle(PHILOSOPHICAL_QUOTES)
    
    quotes_to_process = PHILOSOPHICAL_QUOTES[:TARGET_COUNT]
    print(f"📚 Processando {len(quotes_to_process)} quotes...")
    
    quotes = []
    for i, q in enumerate(quotes_to_process):
        quote_en = q["quote"]
        author_en = q["author"]
        theme = q["theme"]
        
        author_pt = AUTHOR_TRANSlations.get(author_en, author_en)
        
        print(f"  📝 {i+1}/{len(quotes_to_process)}: {author_en}")
        
        quote_pt = translate_text(quote_en)
        
        quotes.append({
            "id": generate_quote_id(),
            "author_en": author_en,
            "quote_en": quote_en,
            "author_pt_br": author_pt,
            "quote_pt_br": quote_pt,
            "source_url": "https://www.gutenberg.org",
            "theme": theme,
            "verified": False
        })
    
    print(f"\n✅ Geradas {len(quotes)} quotes")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Salvo em {OUTPUT_FILE}")
    print("⚠️ IMPORTANTE: Revise as traduções antes de usar!")


if __name__ == "__main__":
    main()