"""England-first Primary Science and Chemistry reference courses.

The catalogue is intentionally authored in English and Estonian first.  The
existing localization layer falls back to English for other interface
languages until their reviewed translations are ready.
"""

from __future__ import annotations

import json
from copy import deepcopy

import sqlalchemy as sa


LANGUAGES = ("en", "et")


def _t(en: str, et: str) -> dict[str, str]:
    return {"en": en, "et": et}


def _lesson(en_title: str, et_title: str, en_body: str, et_body: str, *, duration: int = 20, xp: int = 30) -> dict:
    return {
        "title": _t(en_title, et_title), "content_md": _t(en_body, et_body),
        "content_type": "interactive", "duration_min": duration, "xp_reward": xp,
    }


CATALOG = [
    {
        "title": _t("Primary Science", "Loodusõpetus algkoolile"),
        "slug": "primary-science",
        "description": _t(
            "England Years 1–6 science: observe, test, measure and explain the living world, materials, energy and Earth.",
            "Inglismaa 1.–6. klassi loodusõpetus: vaatle, katseta, mõõda ja selgita elusloodust, materjale, energiat ning Maad.",
        ),
        "category": _t("Science", "Loodusõpetus"), "difficulty": "beginner",
        "modules": [
            {"title": _t("Working Scientifically", "Teaduslik uurimine"), "lessons": [
                _lesson("Questions, Tests and Evidence", "Küsimused, katsed ja tõendid",
                    "# Questions, Tests and Evidence\n\nScience begins with a question. Make one change at a time in a fair test, observe carefully, record what happened and use evidence for your conclusion.\n\n## Good investigators\n\n- predict before testing\n- use equipment safely\n- repeat observations when possible\n- say what the evidence does and does not show\n\nA result that surprises you is useful: it gives you a better question to investigate.",
                    "# Küsimused, katsed ja tõendid\n\nTeadus algab küsimusest. Õiglases katses muuda korraga ainult üht asja, vaatle hoolikalt, kirjuta tulemus üles ja põhjenda järeldust tõenditega.\n\n## Hea uurija\n\n- ennustab enne katset\n- kasutab vahendeid ohutult\n- kordab vaatlusi võimalusel\n- ütleb, mida tõendid näitavad ja mida mitte\n\nÜllatav tulemus on kasulik: see annab parema uurimisküsimuse."),
                _lesson("Measuring and Recording", "Mõõtmine ja tulemuste kirjapanek",
                    "# Measuring and Recording\n\nChoose a suitable unit: centimetres for length, grams for mass, seconds for time and degrees Celsius for temperature. Tables and simple graphs help a pattern become visible.\n\nAlways label a measurement and write enough detail for another investigator to understand your work.",
                    "# Mõõtmine ja tulemuste kirjapanek\n\nVali sobiv ühik: pikkuse jaoks sentimeetrid, massi jaoks grammid, aja jaoks sekundid ja temperatuuri jaoks kraadid Celsiuse järgi. Tabelid ja lihtsad graafikud aitavad mustrit märgata.\n\nMärgista mõõtmine alati ning kirjuta piisavalt täpselt, et teine uurija sinu tööst aru saaks.", duration=15),
            ]},
            {"title": _t("Materials and Matter", "Materjalid ja aine"), "lessons": [
                _lesson("Everyday Materials", "Igapäevased materjalid",
                    "# Everyday Materials\n\nObjects are made from materials. Wood, metal, glass, plastic, fabric and rock have properties that make them useful. Compare hardness, flexibility, transparency, absorbency and waterproofing before choosing a material.\n\nA material is not simply “good” or “bad”: it is suitable for a particular job.",
                    "# Igapäevased materjalid\n\nEsemed on tehtud materjalidest. Puidul, metallil, klaasil, plastil, kangal ja kivimil on omadused, mis muudavad need kasulikuks. Võrdle enne materjali valimist kõvadust, painduvust, läbipaistvust, imavust ja veekindlust.\n\nMaterjal ei ole lihtsalt „hea” või „halb”: see sobib kindlaks otstarbeks."),
                _lesson("Particles, States and Changes", "Osakesed, olekud ja muutused",
                    "# Particles, States and Changes\n\nSolids keep their shape because particles are close together. Liquids flow because particles can move past each other. Gases spread to fill a space. Heating gives particles more energy; cooling removes it.\n\nMelting, freezing, evaporation and condensation are changes of state. No new substance is made.",
                    "# Osakesed, olekud ja muutused\n\nTahked ained hoiavad kuju, sest osakesed on lähestikku. Vedelikud voolavad, sest osakesed saavad üksteisest mööduda. Gaasid levivad, et täita ruum. Kuumutamine annab osakestele energiat; jahutamine võtab seda ära.\n\nSulamine, tahkumine, aurumine ja kondenseerumine on olekumuutused. Uut ainet ei teki."),
                _lesson("Mixtures, Solutions and Separation", "Segud, lahused ja eraldamine",
                    "# Mixtures, Solutions and Separation\n\nA mixture contains substances that have not become a new substance. Use a magnet for iron, a sieve for different-sized solids, filtering for an insoluble solid in liquid, and evaporation to recover a dissolved solid.\n\nDissolving is different from melting: salt in water is still salt and water.",
                    "# Segud, lahused ja eraldamine\n\nSegu sisaldab aineid, mis ei ole muutunud uueks aineks. Raua jaoks kasuta magnetit, eri suurusega tahkete ainete jaoks sõela, vees lahustumatu tahke aine jaoks filtreerimist ning lahustunud tahke aine saamiseks aurutamist.\n\nLahustumine erineb sulamisest: sool vees on ikka sool ja vesi."),
            ]},
            {"title": _t("Living World", "Elusloodus"), "lessons": [
                _lesson("Plants, Animals and Habitats", "Taimed, loomad ja elupaigad",
                    "# Plants, Animals and Habitats\n\nLiving things need resources from their habitats. Plants make food using light. Animals depend on plants or other animals. Classify organisms by observable features and explain how a feature helps an organism survive.",
                    "# Taimed, loomad ja elupaigad\n\nElusolendid vajavad oma elupaigast ressursse. Taimed valmistavad valguse abil toitu. Loomad sõltuvad taimedest või teistest loomadest. Rühmita organisme vaadeldavate tunnuste järgi ja selgita, kuidas tunnus aitab ellu jääda."),
                _lesson("Bodies, Growth and Health", "Keha, kasvamine ja tervis",
                    "# Bodies, Growth and Health\n\nHumans and other animals need balanced nutrition, movement and protection from disease. Skeletons support and protect; muscles make movement possible. Living things grow, reproduce and change over time.",
                    "# Keha, kasvamine ja tervis\n\nInimesed ja teised loomad vajavad tasakaalustatud toitu, liikumist ning kaitset haiguste eest. Luustik toetab ja kaitseb; lihased võimaldavad liikumist. Elusolendid kasvavad, paljunevad ja muutuvad aja jooksul."),
            ]},
            {"title": _t("Energy, Earth and Space", "Energia, Maa ja kosmos"), "lessons": [
                _lesson("Light, Sound and Electricity", "Valgus, heli ja elekter",
                    "# Light, Sound and Electricity\n\nLight travels from sources and reflects from surfaces. Sound is made by vibrations. A complete electrical circuit lets current flow; switches open or close the circuit. Use measurements to compare brightness, volume or distance.",
                    "# Valgus, heli ja elekter\n\nValgus levib allikatest ja peegeldub pindadelt. Heli tekib võnkumisest. Terviklik elektriahel laseb voolul liikuda; lüliti avab või sulgeb ahela. Kasuta mõõtmisi heleduse, valjuse või kauguse võrdlemiseks."),
                _lesson("Earth, Space and Forces", "Maa, kosmos ja jõud",
                    "# Earth, Space and Forces\n\nThe Earth orbits the Sun and rotates once each day. Gravity pulls objects towards Earth. Pushes and pulls can change an object’s motion or shape. Rocks and soils tell stories about processes that change Earth over long periods.",
                    "# Maa, kosmos ja jõud\n\nMaa tiirleb ümber Päikese ning pöörleb kord ööpäevas. Raskusjõud tõmbab objekte Maa poole. Tõuked ja tõmbed võivad muuta objekti liikumist või kuju. Kivimid ja mullad jutustavad protsessidest, mis muudavad Maad pikkade ajavahemike jooksul."),
            ]},
        ],
    },
    {
        "title": _t("Chemistry Fundamentals", "Keemia alused"), "slug": "chemistry-fundamentals",
        "description": _t("England KS3–GCSE chemistry: particles, atoms, bonding, reactions, quantitative chemistry and Earth resources.", "Inglismaa KS3–GCSE keemia: osakesed, aatomid, sidemed, reaktsioonid, arvutuskeemia ja Maa ressursid."),
        "category": _t("Chemistry", "Keemia"), "difficulty": "intermediate",
        "modules": [
            {"title": _t("Particles, Atoms and the Periodic Table", "Osakesed, aatomid ja perioodilisustabel"), "lessons": [
                _lesson("Particle Model and Changes of State", "Osakeste mudel ja olekumuutused", "# Particle Model and Changes of State\n\nUse particle motion and energy transfers to explain density, gas pressure, diffusion and changes of state. A chemical reaction rearranges atoms; a physical change does not create a new substance.", "# Osakeste mudel ja olekumuutused\n\nKasuta osakeste liikumist ja energiaülekandeid tiheduse, gaasirõhu, difusiooni ning olekumuutuste selgitamiseks. Keemiline reaktsioon korraldab aatomeid ümber; füüsikaline muutus uut ainet ei tekita."),
                _lesson("Atoms, Ions and Isotopes", "Aatomid, ioonid ja isotoobid", "# Atoms, Ions and Isotopes\n\nAtomic number is the number of protons. Mass number counts protons and neutrons. Atoms form ions by gaining or losing electrons. Isotopes are atoms of one element with different numbers of neutrons.", "# Aatomid, ioonid ja isotoobid\n\nAatomnumber on prootonite arv. Massiarv loeb prootoneid ja neutroneid. Aatomid moodustavad ioone elektrone loovutades või vastu võttes. Isotoobid on sama elemendi aatomid erineva neutronite arvuga."),
                _lesson("Periodic Table and Reactivity", "Perioodilisustabel ja reaktsioonivõime", "# Periodic Table and Reactivity\n\nElements are arranged by atomic number. Groups have related outer-electron patterns; periods show occupied shells. Use position to predict simple ion charge and trends in reactivity.", "# Perioodilisustabel ja reaktsioonivõime\n\nElemendid on paigutatud aatomnumbri järgi. Rühmadel on sarnased väliselektronide mustrid; perioodid näitavad hõivatud elektronkihte. Kasuta asukohta lihtsa ioonlaengu ja reaktsioonivõime suundumuste ennustamiseks."),
            ]},
            {"title": _t("Bonding and Properties", "Sidemed ja omadused"), "lessons": [
                _lesson("Ionic, Covalent and Metallic Bonding", "Ioon-, kovalentne ja metalliline side", "# Ionic, Covalent and Metallic Bonding\n\nIonic bonds are attractions between oppositely charged ions. Covalent bonds share electrons. Metallic bonding involves positive ions and delocalised electrons. Structure explains melting point, conductivity and solubility.", "# Ioon-, kovalentne ja metalliline side\n\nIoonside on vastasmärgiliste ioonide vaheline tõmme. Kovalentne side jagab elektrone. Metallilises sidemes on positiivsed ioonid ja delokaliseeritud elektronid. Struktuur selgitab sulamispunkti, juhtivust ja lahustuvust."),
                _lesson("Giant Structures and Materials", "Hiigelstruktuurid ja materjalid", "# Giant Structures and Materials\n\nDiamond, graphite, graphene, metals and ionic lattices have different particle arrangements. Relate each arrangement to strength, hardness, conductivity and uses.", "# Hiigelstruktuurid ja materjalid\n\nTeemandil, grafiidil, grafeenil, metallidel ja ioonvõredel on erinev osakeste paigutus. Seo iga paigutus tugevuse, kõvaduse, juhtivuse ja kasutusaladega."),
            ]},
            {"title": _t("Reactions and Quantitative Chemistry", "Reaktsioonid ja arvutuskeemia"), "lessons": [
                _lesson("Equations and Conservation", "Võrrandid ja jäävusseadus", "# Equations and Conservation\n\nBalanced symbol equations conserve atoms. Coefficients change amounts, never the chemical formula. Include state symbols when useful and identify reactants and products.", "# Võrrandid ja jäävusseadus\n\nTasakaalustatud sümbolvõrrandid säilitavad aatomite arvu. Kordajad muudavad koguseid, mitte kunagi keemilist valemit. Vajadusel lisa olekusümbolid ning erista lähteained ja saadused."),
                _lesson("Moles, Masses and Concentration", "Moolid, massid ja kontsentratsioon", "# Moles, Masses and Concentration\n\nThe mole links mass, particle number and formula mass. Use a balanced equation as a ratio to calculate reacting masses, gas volumes, concentration and yield. Show units at every step.", "# Moolid, massid ja kontsentratsioon\n\nMool seob massi, osakeste arvu ja valemmassi. Kasuta tasakaalustatud võrrandit suhtena reageerivate masside, gaasimahtude, kontsentratsiooni ja saagise arvutamiseks. Näita ühikuid igal sammul."),
                _lesson("Acids, Bases, Redox and Electrolysis", "Happed, alused, redoks ja elektrolüüs", "# Acids, Bases, Redox and Electrolysis\n\nAcids react with metals, bases and carbonates. Neutralisation makes salt and water. Redox transfers electrons. Electrolysis uses electrical energy to decompose ionic compounds.", "# Happed, alused, redoks ja elektrolüüs\n\nHapped reageerivad metallide, aluste ja karbonaatidega. Neutraliseerimine annab soola ja vee. Redoksreaktsioonis kanduvad elektronid üle. Elektrolüüs kasutab elektrienergiat ioonsete ühendite lagundamiseks."),
            ]},
            {"title": _t("Energy, Rates and Resources", "Energia, kiirused ja ressursid"), "lessons": [
                _lesson("Energy Changes and Reaction Rates", "Energiimuutused ja reaktsioonikiirused", "# Energy Changes and Reaction Rates\n\nExothermic reactions transfer energy to surroundings; endothermic reactions take it in. Collision theory explains why temperature, concentration, surface area and catalysts change rate.", "# Energiimuutused ja reaktsioonikiirused\n\nEksotermilised reaktsioonid annavad energiat ümbritsevale; endotermilised võtavad seda sisse. Põrgeteooria selgitab, miks temperatuur, kontsentratsioon, pindala ja katalüsaatorid muudavad kiirust."),
                _lesson("Earth Chemistry, Organic Chemistry and Analysis", "Maa keemia, orgaaniline keemia ja analüüs", "# Earth Chemistry, Organic Chemistry and Analysis\n\nChemistry helps use finite resources responsibly. Carbon compounds form families with related reactions. Learn basic tests for gases and ions, chromatography and the difference between pure substances and mixtures.", "# Maa keemia, orgaaniline keemia ja analüüs\n\nKeemia aitab kasutada piiratud ressursse vastutustundlikult. Süsinikuühendid moodustavad sarnaste reaktsioonidega perekondi. Õpi gaaside ja ioonide põhiteste, kromatograafiat ning puhaste ainete ja segude erinevust."),
            ]},
        ],
    },
    {
        "title": _t("Advanced Chemistry", "Edasijõudnute keemia"), "slug": "advanced-chemistry",
        "description": _t("A-level to first-year university bridge in physical, organic and inorganic chemistry with practical data skills.", "Sild A-taseme ja ülikooli esimese aasta vahel füüsikalises, orgaanilises ja anorgaanilises keemias ning praktilistes andmeoskustes."),
        "category": _t("Chemistry", "Keemia"), "difficulty": "advanced",
        "modules": [
            {"title": _t("Physical Chemistry", "Füüsikaline keemia"), "lessons": [
                _lesson("Orbitals, Spectra and Structure", "Orbitaalid, spektrid ja struktuur", "# Orbitals, Spectra and Structure\n\nUse sub-shells, orbitals and electron configuration to explain periodicity. Interpret simple mass spectra and link molecular shape to electron-pair repulsion.", "# Orbitaalid, spektrid ja struktuur\n\nKasuta alamkihte, orbitaale ja elektronkonfiguratsiooni perioodilisuse selgitamiseks. Tõlgenda lihtsaid massispektreid ning seo molekuli kuju elektronpaaride tõukumisega."),
                _lesson("Thermodynamics, Kinetics and Equilibrium", "Termodünaamika, kineetika ja tasakaal", "# Thermodynamics, Kinetics and Equilibrium\n\nUse enthalpy, entropy and free-energy ideas to reason about feasibility. Model rates with rate equations and activation energy. At equilibrium, forward and reverse rates are equal; use Kc and Le Chatelier’s principle carefully.", "# Termodünaamika, kineetika ja tasakaal\n\nKasuta entalpia, entroopia ja vabaenergia ideid reaktsioonide võimalikkuse põhjendamiseks. Modelleeri kiirusi kiirusvõrrandite ja aktiveerimisenergiaga. Tasakaalus on edasi- ja tagasireaktsiooni kiirused võrdsed; kasuta Kc-d ja Le Chatelier’ printsiipi hoolikalt."),
                _lesson("Acids, Electrochemistry and Measurement", "Happed, elektrokeemia ja mõõtmine", "# Acids, Electrochemistry and Measurement\n\nCalculate pH, Ka and buffer behaviour with assumptions stated. Build cell diagrams, compare electrode potentials and report uncertainty, significant figures and anomalous data honestly.", "# Happed, elektrokeemia ja mõõtmine\n\nArvuta pH, Ka ja puhverlahuste käitumine koos eeldustega. Koosta elemendiskeeme, võrdle elektroodipotentsiaale ning esita määramatus, tüvenumbrid ja hälbivad andmed ausalt."),
            ]},
            {"title": _t("Organic Chemistry I", "Orgaaniline keemia I"), "lessons": [
                _lesson("Structure, Stereochemistry and Naming", "Struktuur, stereokeemia ja nimetamine", "# Structure, Stereochemistry and Naming\n\nRepresent organic compounds with displayed, structural and skeletal formulas. Identify functional groups, homologous series, stereocentres and E/Z or cis/trans isomerism where appropriate.", "# Struktuur, stereokeemia ja nimetamine\n\nEsita orgaanilisi ühendeid välja kirjutatud, struktuuri- ja skeletivalemiga. Tuvasta funktsionaalrühmad, homoloogilised read, stereokeskmed ning vajadusel E/Z või cis/trans isomeeria."),
                _lesson("Mechanisms and Synthesis", "Mehhanismid ja süntees", "# Mechanisms and Synthesis\n\nUse curly arrows to account for electron pairs in substitution, elimination, addition and carbonyl reactions. Plan short syntheses by tracking functional-group changes, selectivity, yield and purification.", "# Mehhanismid ja süntees\n\nKasuta kaarnoolekesi elektronpaaride liikumise kirjeldamiseks asendus-, eliminatsiooni-, liitumis- ja karbonüülreaktsioonides. Plaani lühisünteese, jälgides funktsionaalrühmade muutusi, selektiivsust, saagist ja puhastamist."),
                _lesson("Spectroscopy and Structure Elucidation", "Spektroskoopia ja struktuuri määramine", "# Spectroscopy and Structure Elucidation\n\nCombine accurate mass, fragmentation, infrared absorption and 1H/13C NMR evidence. A proposed structure is credible only when every major datum is explained.", "# Spektroskoopia ja struktuuri määramine\n\nÜhenda täpne mass, fragmenteerumine, infrapunaneeldumine ning 1H/13C NMR-i tõendid. Pakutud struktuur on usutav vaid siis, kui iga oluline andmepunkt on selgitatud."),
            ]},
            {"title": _t("Inorganic Chemistry I", "Anorgaaniline keemia I"), "lessons": [
                _lesson("Periodicity and Redox", "Perioodilisus ja redoks", "# Periodicity and Redox\n\nExplain trends using nuclear charge, shielding and structure. Balance redox equations with oxidation states and consider why chemical choices have environmental and industrial consequences.", "# Perioodilisus ja redoks\n\nSelgita suundumusi tuumalaengu, varjestuse ja struktuuriga. Tasakaalusta redoksvõrrandeid oksüdatsiooniastmete abil ning mõtle, miks keemilistel valikutel on keskkonna- ja tööstuslikud tagajärjed."),
                _lesson("Coordination Chemistry and Materials", "Koordinatsioonikeemia ja materjalid", "# Coordination Chemistry and Materials\n\nDescribe ligands, coordination number, geometry, isomerism and colour in transition-metal complexes. Relate crystal and solid-state structure to magnetic, optical and conductive properties.", "# Koordinatsioonikeemia ja materjalid\n\nKirjelda ligande, koordinatsiooniarvu, geomeetriat, isomeeriat ja värvust siirdemetallikompleksides. Seo kristall- ja tahkisstruktuur magnetiliste, optiliste ning juhtivusomadustega."),
            ]},
            {"title": _t("Practical Chemistry and Data", "Praktiline keemia ja andmed"), "lessons": [
                _lesson("Designing Reliable Investigations", "Usaldusväärsete uurimuste kavandamine", "# Designing Reliable Investigations\n\nChoose controls, measurements and a safe method that answer a focused question. Distinguish accuracy, precision, repeatability and reproducibility. Use uncertainty to judge a claim rather than hiding imperfect data.", "# Usaldusväärsete uurimuste kavandamine\n\nVali kontrollid, mõõtmised ja ohutu meetod, mis vastavad täpsele küsimusele. Erista täpsust, kordustäpsust ja reprodutseeritavust. Kasuta määramatust väite hindamiseks, mitte ebatäiuslike andmete peitmiseks."),
            ]},
        ],
    },
]


EXERCISES = [
    {
        "source_key": "fl-primary-particle-state", "course_slug": "primary-science", "lesson": "Particles, States and Changes",
        "exercise_type": "molecule_geometry", "concepts": ["states-of-matter", "particle-model"], "difficulty_band": 1,
        "prompt": _t("Warm the model, then choose the state where particles are closest together.", "Soojenda mudelit, seejärel vali olek, kus osakesed on kõige lähestikku."),
        "public": {"choices": _t(["Solid", "Liquid", "Gas"], ["Tahke", "Vedelik", "Gaas"]), "choice_labels": _t(["Solid", "Liquid", "Gas"], ["Tahke", "Vedelik", "Gaas"]), "molecule": "water", "scene": "particle-state", "ui": _t({"check": "Check answer", "reset": "Reset view", "heat": "Heat", "cool": "Cool", "level": "Guided science"}, {"check": "Kontrolli vastust", "reset": "Lähtesta vaade", "heat": "Soojenda", "cool": "Jahuta", "level": "Juhendatud loodusõpetus"})},
        "answer": {"choice": 0},
    },
    {
        "source_key": "fl-primary-material-choice", "course_slug": "primary-science", "lesson": "Everyday Materials",
        "exercise_type": "material_sort", "concepts": ["materials", "properties"], "difficulty_band": 1,
        "prompt": _t("Choose the best material for a waterproof raincoat.", "Vali veekindla vihmamantli jaoks parim materjal."),
        "public": {"choices": _t(["Absorbent paper", "Waterproof fabric", "Glass"], ["Imav paber", "Veekindel kangas", "Klaas"]), "ui": _t({"check": "Check answer", "level": "Guided science"}, {"check": "Kontrolli vastust", "level": "Juhendatud loodusõpetus"})},
        "answer": {"choice": 1},
    },
    {
        "source_key": "fl-chem-atom-sodium", "course_slug": "chemistry-fundamentals", "lesson": "Atoms, Ions and Isotopes",
        "exercise_type": "atom_builder", "concepts": ["atomic-structure", "ions"], "difficulty_band": 2,
        "prompt": _t("Build a neutral sodium-23 atom: choose its protons, neutrons and electrons.", "Koosta neutraalne naatrium-23 aatom: vali prootonite, neutronite ja elektronide arv."),
        "public": {"atom": "Na", "mass_number": 23, "atomic_number": 11, "ui": _t({"check": "Check atom", "level": "Guided chemistry", "protons": "Protons", "neutrons": "Neutrons", "electrons": "Electrons"}, {"check": "Kontrolli aatomit", "level": "Juhendatud keemia", "protons": "Prootonid", "neutrons": "Neutronid", "electrons": "Elektronid"})},
        "answer": {"protons": 11, "neutrons": 12, "electrons": 11},
    },
    {
        "source_key": "fl-chem-balance-water", "course_slug": "chemistry-fundamentals", "lesson": "Equations and Conservation",
        "exercise_type": "equation_balance", "concepts": ["balanced-equations", "conservation"], "difficulty_band": 2,
        "prompt": _t("Balance the equation H₂ + O₂ → H₂O. Enter coefficients from left to right.", "Tasakaalusta võrrand H₂ + O₂ → H₂O. Sisesta kordajad vasakult paremale."),
        "public": {"equation": ["H₂", "O₂", "H₂O"], "ui": _t({"check": "Check equation", "level": "Guided chemistry", "coefficient": "Coefficient"}, {"check": "Kontrolli võrrandit", "level": "Juhendatud keemia", "coefficient": "Kordaja"})},
        "answer": {"coefficients": [2, 1, 2]},
    },
    {
        "source_key": "fl-chem-water-geometry", "course_slug": "chemistry-fundamentals", "lesson": "Ionic, Covalent and Metallic Bonding",
        "exercise_type": "molecule_geometry", "concepts": ["covalent-bonding", "molecular-shape"], "difficulty_band": 2,
        "prompt": _t("Inspect water in 3D. Which description fits its bonding?", "Uuri vett 3D-s. Milline kirjeldus sobib selle sidemega?"),
        "public": {"choices": _t(["Covalent bonds share electrons", "Ionic bonds transfer all atoms", "Metallic bonds form molecules"], ["Kovalentne side jagab elektrone", "Ioonside kannab üle kõik aatomid", "Metalliline side moodustab molekule"]), "molecule": "water", "scene": "molecule", "ui": _t({"check": "Check answer", "reset": "Reset view", "level": "Guided chemistry"}, {"check": "Kontrolli vastust", "reset": "Lähtesta vaade", "level": "Juhendatud keemia"})},
        "answer": {"choice": 0},
    },
    {
        "source_key": "fl-chem-moles-water", "course_slug": "chemistry-fundamentals", "lesson": "Moles, Masses and Concentration",
        "exercise_type": "mole_calculation", "concepts": ["moles", "formula-mass"], "difficulty_band": 3,
        "prompt": _t("How many moles are in 36.0 g of water (Mr = 18.0)?", "Mitu mooli on 36,0 g vees (Mr = 18,0)?"),
        "public": {"unit": "mol", "ui": _t({"check": "Check calculation", "level": "Guided chemistry", "answer": "Answer"}, {"check": "Kontrolli arvutust", "level": "Juhendatud keemia", "answer": "Vastus"})},
        "answer": {"value": 2.0, "tolerance": 0.01},
    },
    {
        "source_key": "fl-advanced-vsepr-water", "course_slug": "advanced-chemistry", "lesson": "Orbitals, Spectra and Structure",
        "exercise_type": "molecule_geometry", "concepts": ["vsepr", "lone-pairs"], "difficulty_band": 4,
        "prompt": _t("Rotate the 3D water model. Which molecular shape is predicted by VSEPR?", "Pööra 3D veemudelit. Millist molekulikuju ennustab VSEPR?"),
        "public": {"choices": _t(["Bent", "Linear", "Tetrahedral"], ["Nurgeline", "Lineaarne", "Tetraeedriline"]), "molecule": "water", "scene": "vsepr", "ui": _t({"check": "Check geometry", "reset": "Reset view", "level": "Advanced chemistry"}, {"check": "Kontrolli geomeetriat", "reset": "Lähtesta vaade", "level": "Edasijõudnute keemia"})},
        "answer": {"choice": 0},
    },
    {
        "source_key": "fl-advanced-spectra-ethanol", "course_slug": "advanced-chemistry", "lesson": "Spectroscopy and Structure Elucidation",
        "exercise_type": "spectra_choice", "concepts": ["infrared", "functional-groups"], "difficulty_band": 4,
        "prompt": _t("An IR spectrum has a broad O–H absorption. Which functional group is most strongly indicated?", "IR-spektris on lai O–H neeldumisriba. Millisele funktsionaalrühmale see kõige tugevamalt viitab?"),
        "public": {"choices": _t(["Alcohol", "Alkene", "Halogenoalkane"], ["Alkohol", "Alkeen", "Halogenoalkaan"]), "chart": "ir-oh", "ui": _t({"check": "Check interpretation", "level": "Advanced chemistry"}, {"check": "Kontrolli tõlgendust", "level": "Edasijõudnute keemia"})},
        "answer": {"choice": 0},
    },
    {
        "source_key": "fl-advanced-mechanism-choice", "course_slug": "advanced-chemistry", "lesson": "Mechanisms and Synthesis",
        "exercise_type": "mechanism_choice", "concepts": ["organic-mechanisms", "electron-pairs"], "difficulty_band": 5,
        "prompt": _t("For a nucleophile attacking a positive carbon centre, what does the first curly arrow show?", "Kui nukleofiil ründab positiivset süsinikukeskust, mida näitab esimene kaarnooleke?"),
        "public": {"choices": _t(["A lone pair moving towards carbon", "A proton becoming a neutron", "A bond gaining mass"], ["Üksik elektronpaar liigub süsiniku poole", "Prooton muutub neutroniks", "Side kogub massi"]), "ui": _t({"check": "Check mechanism", "level": "Advanced chemistry"}, {"check": "Kontrolli mehhanismi", "level": "Edasijõudnute keemia"})},
        "answer": {"choice": 0},
    },
]


def _english(value):
    if isinstance(value, dict) and set(value).issubset(set(LANGUAGES)):
        return value["en"]
    if isinstance(value, list):
        return [_english(item) for item in value]
    if isinstance(value, dict):
        return {key: _english(item) for key, item in value.items()}
    return value


def _course_translations(course: dict) -> list[tuple[str, str, str | None, str | None]]:
    rows = [("courses", course["slug"], course["title"]["et"], course["description"]["et"])]
    for module in course["modules"]:
        for lesson in module["lessons"]:
            rows.append(("lessons", lesson["title"]["en"], lesson["title"]["et"], lesson["content_md"]["et"]))
    return rows


def public_exercise(exercise: dict, lang: str = "en") -> dict:
    language = lang if lang in LANGUAGES else "en"
    public = deepcopy(exercise["public"])
    for key, value in list(public.items()):
        if isinstance(value, dict) and set(value).issubset(set(LANGUAGES)):
            public[key] = value[language]
    return {
        "source_key": exercise["source_key"], "engine": "chemistry", "exercise_type": exercise["exercise_type"],
        "prompt": exercise["prompt"][language], "concepts": exercise["concepts"],
        "difficulty_band": exercise["difficulty_band"], "cognitive_layer": "skill", **public,
    }


def seed_science_courses(conn, schema: str) -> list[dict]:
    """Install all three curriculum courses without deleting teacher work."""
    owner_id = conn.execute(sa.text(f"SELECT id FROM {schema}.users WHERE lower(email)='kaljuvee@gmail.com' LIMIT 1")).scalar()
    result = []
    lessons_by_course: dict[str, dict[str, int]] = {}
    for source in CATALOG:
        course = _english(source)
        saved = conn.execute(sa.text(f"""
            INSERT INTO {schema}.courses (title, slug, description, category, difficulty, is_published, instructor_id, is_default)
            VALUES (:title, :slug, :description, :category, :difficulty, true, :owner, true)
            ON CONFLICT (slug) DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description,
                category=EXCLUDED.category, difficulty=EXCLUDED.difficulty, is_published=true, is_default=true,
                instructor_id=COALESCE(EXCLUDED.instructor_id, {schema}.courses.instructor_id)
            RETURNING *
        """), {**{key: course[key] for key in ("title", "slug", "description", "category", "difficulty")}, "owner": owner_id}).mappings().one()
        lesson_ids: dict[str, int] = {}
        for module_index, module in enumerate(course["modules"]):
            module_id = conn.execute(sa.text(f"SELECT id FROM {schema}.modules WHERE course_id=:course AND title=:title ORDER BY id LIMIT 1"), {"course": saved["id"], "title": module["title"]}).scalar()
            if module_id:
                conn.execute(sa.text(f"UPDATE {schema}.modules SET order_idx=:order_idx WHERE id=:id"), {"order_idx": module_index, "id": module_id})
            else:
                module_id = conn.execute(sa.text(f"INSERT INTO {schema}.modules (course_id,title,order_idx) VALUES (:course,:title,:order_idx) RETURNING id"), {"course": saved["id"], "title": module["title"], "order_idx": module_index}).scalar_one()
            source_module = source["modules"][module_index]
            conn.execute(sa.text(f"""INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title)
                VALUES ('modules',:id,'et',:title)
                ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title"""),
                {"id": module_id, "title": source_module["title"]["et"]})
            for lesson_index, lesson in enumerate(module["lessons"]):
                lesson_id = conn.execute(sa.text(f"SELECT id FROM {schema}.lessons WHERE module_id=:module AND title=:title ORDER BY id LIMIT 1"), {"module": module_id, "title": lesson["title"]}).scalar()
                params = {"module": module_id, "title": lesson["title"], "content": lesson["content_md"], "duration": lesson["duration_min"], "xp": lesson["xp_reward"], "order_idx": lesson_index}
                if lesson_id:
                    conn.execute(sa.text(f"UPDATE {schema}.lessons SET content_md=:content, content_type='interactive', duration_min=:duration, xp_reward=:xp, order_idx=:order_idx WHERE id=:id"), {**params, "id": lesson_id})
                else:
                    lesson_id = conn.execute(sa.text(f"INSERT INTO {schema}.lessons (module_id,title,content_md,content_type,duration_min,xp_reward,order_idx) VALUES (:module,:title,:content,'interactive',:duration,:xp,:order_idx) RETURNING id"), params).scalar_one()
                lesson_ids[lesson["title"]] = lesson_id
        # English is stored on the base rows; Estonian is stored as entity translations.
        for entity_type, english_title, et_title, et_content in _course_translations(source):
            if entity_type == "courses":
                entity_id = saved["id"]
                conn.execute(sa.text(f"""INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,description)
                    VALUES ('courses',:id,'et',:title,:description)
                    ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title,description=EXCLUDED.description"""), {"id": entity_id, "title": et_title, "description": et_content})
            else:
                entity_id = lesson_ids[english_title]
                conn.execute(sa.text(f"""INSERT INTO {schema}.content_translations (entity_type,entity_id,language,title,content_md)
                    VALUES ('lessons',:id,'et',:title,:content)
                    ON CONFLICT (entity_type,entity_id,language) DO UPDATE SET title=EXCLUDED.title,content_md=EXCLUDED.content_md"""), {"id": entity_id, "title": et_title, "content": et_content})
        lessons_by_course[source["slug"]] = lesson_ids
        result.append(dict(saved))

    for exercise in EXERCISES:
        public = public_exercise(exercise, "en")
        prompt = public.pop("prompt")
        public.pop("source_key", None)
        public.pop("engine", None)
        public.pop("exercise_type", None)
        public.pop("concepts", None)
        public.pop("difficulty_band", None)
        public.pop("cognitive_layer", None)
        exercise_id = conn.execute(sa.text(f"""
            INSERT INTO {schema}.interactive_exercises (source_key,engine,exercise_type,prompt,concepts,difficulty_band,cognitive_layer,public_payload,answer_payload)
            VALUES (:source_key,'chemistry',:exercise_type,:prompt,CAST(:concepts AS jsonb),:band,'skill',CAST(:public AS jsonb),CAST(:answer AS jsonb))
            ON CONFLICT (source_key) DO UPDATE SET engine='chemistry',exercise_type=EXCLUDED.exercise_type,prompt=EXCLUDED.prompt,
                concepts=EXCLUDED.concepts,difficulty_band=EXCLUDED.difficulty_band,cognitive_layer='skill',public_payload=EXCLUDED.public_payload,answer_payload=EXCLUDED.answer_payload
            RETURNING id
        """), {"source_key": exercise["source_key"], "exercise_type": exercise["exercise_type"], "prompt": prompt, "concepts": json.dumps(exercise["concepts"]), "band": exercise["difficulty_band"], "public": json.dumps(public), "answer": json.dumps(exercise["answer"])}).scalar_one()
        lesson_id = lessons_by_course[exercise["course_slug"]][exercise["lesson"]]
        conn.execute(sa.text(f"""INSERT INTO {schema}.lesson_exercises (lesson_id,exercise_id,order_idx)
            VALUES (:lesson,:exercise,0) ON CONFLICT (lesson_id,exercise_id) DO UPDATE SET order_idx=EXCLUDED.order_idx"""), {"lesson": lesson_id, "exercise": exercise_id})
        localized = public_exercise(exercise, "et")
        localized.pop("source_key", None); localized.pop("engine", None); localized.pop("exercise_type", None)
        localized.pop("concepts", None); localized.pop("difficulty_band", None); localized.pop("cognitive_layer", None)
        et_prompt = localized.pop("prompt")
        conn.execute(sa.text(f"""INSERT INTO {schema}.exercise_translations (exercise_id,language,prompt,public_payload)
            VALUES (:exercise,'et',:prompt,CAST(:public AS jsonb))
            ON CONFLICT (exercise_id,language) DO UPDATE SET prompt=EXCLUDED.prompt,public_payload=EXCLUDED.public_payload"""), {"exercise": exercise_id, "prompt": et_prompt, "public": json.dumps(localized)})
    return result
