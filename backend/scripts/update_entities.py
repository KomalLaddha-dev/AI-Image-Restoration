"""
Update monuments.json with curated historical figures, significance, and timelines.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
monuments_path = DATA_DIR / "monuments.json"

with open(monuments_path, "r", encoding="utf-8") as f:
    items = json.load(f)

existing_ids = {m["id"] for m in items}

new_figures = [
  {
    "id": "mahatma_gandhi",
    "name": "Mahatma Gandhi",
    "category": "historical_figure",
    "location": "Porbandar & New Delhi, India",
    "coordinates": [28.6139, 77.2090],
    "era": "1869–1948 CE",
    "builder": "Father of the Nation, Freedom Fighter",
    "architectural_style": "Philosophy of Satyagraha & Ahimsa (Nonviolence)",
    "unesco_status": "Recognized by UN International Day of Non-Violence (Oct 2)",
    "significance": "Pioneered the philosophy and strategy of nonviolent civil disobedience (Satyagraha) that liberated India from colonial rule and inspired international civil rights and freedom movements worldwide, including those led by Martin Luther King Jr. and Nelson Mandela.",
    "timeline": [
      {"year": "1869", "event": "Born in Porbandar, Gujarat, India."},
      {"year": "1893", "event": "Arrives in South Africa; develops the strategy of Satyagraha (truth-force) over 21 years."},
      {"year": "1915", "event": "Returns to India and leads nationwide peasant and labor movements in Champaran and Kheda."},
      {"year": "1930", "event": "Leads the iconic 240-mile Salt March to Dandi, shaking the economic and moral foundations of British rule."},
      {"year": "1942", "event": "Launches the Quit India Movement demanding an immediate British exit."},
      {"year": "1947", "event": "India achieves freedom; Gandhi conducts fasts unto death to restore communal harmony."},
      {"year": "1948", "event": "Martyred in New Delhi; celebrated universally as a global icon of peace and liberty."}
    ]
  },
  {
    "id": "swami_vivekananda",
    "name": "Swami Vivekananda",
    "category": "historical_figure",
    "location": "Kolkata & Belur Math, India",
    "coordinates": [22.6322, 88.3562],
    "era": "1863–1902 CE",
    "builder": "Monk, Philosopher, Founder of Ramakrishna Mission",
    "architectural_style": "Advaita Vedanta & Modern Indian Philosophy",
    "unesco_status": "National Youth Day (Jan 12) & Global Interfaith Pioneer",
    "significance": "Introduced the ancient Indian philosophical schools of Vedanta and Yoga to the Western world with his historic 1893 address at the Parliament of Religions in Chicago. Revitalized India's cultural confidence and spiritual renaissance, advocating selfless service to humanity.",
    "timeline": [
      {"year": "1863", "event": "Born Narendranath Datta in Kolkata, Bengal."},
      {"year": "1881", "event": "Meets mystic master Sri Ramakrishna Paramahamsa at Dakshineswar."},
      {"year": "1893", "event": "Delivers his epochal speech ('Sisters and brothers of America') at the Parliament of Religions in Chicago."},
      {"year": "1897", "event": "Founds the Ramakrishna Mission for universal human service, relief, and education."},
      {"year": "1899", "event": "Establishes Belur Math as the monastic headquarters of the Ramakrishna Order."},
      {"year": "1902", "event": "Attains Mahasamadhi at Belur Math at age 39, leaving an immortal intellectual legacy."}
    ]
  },
  {
    "id": "subhas_chandra_bose",
    "name": "Netaji Subhas Chandra Bose",
    "category": "historical_figure",
    "location": "Cuttack & Kolkata, India",
    "coordinates": [20.4625, 85.8828],
    "era": "1897–1945 CE",
    "builder": "Supreme Commander of Azad Hind Fauj (INA)",
    "architectural_style": "Revolutionary Nationalism & Military Leadership",
    "unesco_status": "Celebrated on Parakram Diwas (Jan 23)",
    "significance": "Led the armed freedom struggle for India's liberation as Supreme Commander of the Indian National Army (Azad Hind Fauj). Coined the immortal national greeting 'Jai Hind' and mobilized thousands across Asia, delivering decisive blows to British imperial confidence.",
    "timeline": [
      {"year": "1897", "event": "Born in Cuttack, Orissa Division."},
      {"year": "1920", "event": "Ranks 4th in the Indian Civil Service exam in London, but resigns to join the national freedom movement."},
      {"year": "1938", "event": "Elected President of the Indian National Congress at Haripura."},
      {"year": "1941", "event": "Executes the 'Great Escape' from British house arrest in Kolkata to Europe and Southeast Asia."},
      {"year": "1943", "event": "Proclaims the Provisional Government of Free India (Arzi Hukumat-e-Azad Hind) and takes command of INA."},
      {"year": "1944", "event": "INA troops raise the Indian tricolor in Moirang, Manipur on Indian soil."},
      {"year": "1945", "event": "Reported martyred following a plane crash; revered across the nation as Netaji."}
    ]
  },
  {
    "id": "br_ambedkar",
    "name": "Dr. B. R. Ambedkar",
    "category": "historical_figure",
    "location": "Mhow & New Delhi, India",
    "coordinates": [22.5539, 75.7638],
    "era": "1891–1956 CE",
    "builder": "Chief Architect of Indian Constitution, 1st Law Minister",
    "architectural_style": "Constitutionalism, Social Justice & Jurisprudence",
    "unesco_status": "Conferred Bharat Ratna (1990) & World Human Rights Pioneer",
    "significance": "Chief architect of the Constitution of India, world-renowned jurist, and economist who led the historic movement for Dalit rights and the eradication of social untouchability. Enshrined equal rights, civil liberties, and progressive labor laws into the foundation of the world's largest democracy.",
    "timeline": [
      {"year": "1891", "event": "Born in Mhow, Central Provinces (Madhya Pradesh)."},
      {"year": "1915", "event": "Earns master's and PhD from Columbia University, New York, and D.Sc from London School of Economics."},
      {"year": "1927", "event": "Leads the Mahad Satyagraha to claim equal public water access for Dalits."},
      {"year": "1932", "event": "Concludes the Poona Pact with Mahatma Gandhi for reserved legislative seats."},
      {"year": "1947", "event": "Appointed independent India's first Law Minister and Chairman of the Constitution Drafting Committee."},
      {"year": "1950", "event": "The Constitution of India drafted under his leadership takes effect on January 26."},
      {"year": "1956", "event": "Embraces Buddhism alongside 500,000 followers at Deekshabhoomi, Nagpur."}
    ]
  },
  {
    "id": "albert_einstein",
    "name": "Albert Einstein",
    "category": "historical_figure",
    "location": "Ulm (Germany) & Princeton (USA)",
    "coordinates": [40.3440, -74.6514],
    "era": "1879–1955 CE",
    "builder": "Theoretical Physicist, Nobel Laureate",
    "architectural_style": "Theoretical Physics & Relativistic Cosmology",
    "unesco_status": "1921 Nobel Prize in Physics & Time Person of the Century",
    "significance": "Fundamentally transformed our understanding of space, time, gravity, and energy. Formulated the Special and General Theories of Relativity and the mass-energy equivalence equation E=mc^2. His Nobel Prize-winning work on the photoelectric effect was pivotal to the emergence of quantum physics.",
    "timeline": [
      {"year": "1879", "event": "Born in Ulm, Kingdom of Württemberg, Germany."},
      {"year": "1905", "event": "Annus Mirabilis: publishes 4 revolutionary papers on the photoelectric effect, Brownian motion, and special relativity."},
      {"year": "1915", "event": "Completes the General Theory of Relativity, proving gravity is the geometric warping of spacetime."},
      {"year": "1919", "event": "Sir Arthur Eddington's solar eclipse expedition experimentally verifies gravitational light bending."},
      {"year": "1921", "event": "Awarded the Nobel Prize in Physics for his discovery of the law of the photoelectric effect."},
      {"year": "1933", "event": "Immigrates to the United States and joins the Institute for Advanced Study in Princeton."},
      {"year": "1955", "event": "Passes away in Princeton, New Jersey, celebrated as the greatest scientist of the modern era."}
    ]
  },
  {
    "id": "abraham_lincoln",
    "name": "Abraham Lincoln",
    "category": "historical_figure",
    "location": "Kentucky & Washington, D.C., USA",
    "coordinates": [38.8951, -77.0364],
    "era": "1809–1865 CE",
    "builder": "16th President of the United States",
    "architectural_style": "Democratic Statesmanship & Constitutional Union",
    "unesco_status": "Signer of Emancipation Proclamation & Lincoln Memorial",
    "significance": "Preserved the United States through its greatest existential crisis, the American Civil War, while defeating the Confederacy. Issued the Emancipation Proclamation and secured the Thirteenth Amendment, legally abolishing slavery in the United States and elevating democracy to its highest moral ground.",
    "timeline": [
      {"year": "1809", "event": "Born in a humble one-room log cabin in Hardin County, Kentucky."},
      {"year": "1860", "event": "Elected the 16th President of the United States."},
      {"year": "1861", "event": "Civil War begins; mobilizes the Union to preserve constitutional government."},
      {"year": "1863", "event": "Issues the Emancipation Proclamation freeing slaves in rebel states and delivers the Gettysburg Address."},
      {"year": "1865", "event": "Pushes through the 13th Amendment abolishing slavery; delivers Second Inaugural ('With malice toward none')."},
      {"year": "1865", "event": "Assassinated by John Wilkes Booth at Ford's Theatre just days after the Confederate surrender."}
    ]
  }
]

added = 0
for f in new_figures:
    if f["id"] not in existing_ids:
        items.append(f)
        added += 1

with open(monuments_path, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Successfully updated monuments.json: total={len(items)}, added={added}")
