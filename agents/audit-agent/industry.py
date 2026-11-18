"""Industry profiles: what "converting a visitor" means differs by business.

A dentist converts with a booked appointment, a home care agency with a care-assessment request, a contractor
with a quote request, a realtor with a home valuation or property search. detect() works out the industry from
the lead form, structured data and the site's own words; checks() runs the conversion checks that fit it;
IMPACT overrides the "what it costs you" lines that read differently per industry.
"""
from __future__ import annotations

import re

# key: (label, search term for keyword research, detection keywords, schema.org types)
INDUSTRIES = {
    "home_care": ("Home care", "home care", ("home care", "home health", "in-home care", "caregiver", "senior care",
                  "personal care aide", "home health aide", "cdpap", "companion care", "elder care", "hha"),
                  ("homehealthcare", "homecare")),
    "senior_living": ("Senior living", "assisted living", ("assisted living", "memory care", "senior living",
                      "nursing home", "skilled nursing", "rehabilitation center"), ("nursinghome", "assistedliving")),
    "dental": ("Dental", "dentist", ("dentist", "dental", "orthodont", "invisalign", "teeth whitening", "implants"),
               ("dentist",)),
    "medical": ("Medical practice", "doctor", ("physician", "clinic", "urgent care", "pediatric", "dermatolog",
                "chiropract", "physical therapy", "medical practice", "primary care", "therapist", "psychiatr"),
                ("medicalclinic", "physician", "medicalbusiness", "chiropractor", "physiotherapy", "medicalorganization")),
    "legal": ("Law firm", "lawyer", ("attorney", "law firm", "lawyer", "legal services", "personal injury",
              "immigration law", "divorce"), ("legalservice", "attorney", "lawfirm")),
    "home_services": ("Home services / contractor", "contractor", ("plumb", "hvac", "roofing", "roofer", "electrician",
                      "contractor", "remodel", "renovation", "landscap", "pest control", "cleaning service",
                      "handyman", "painting", "flooring", "moving company", "movers", "locksmith"),
                      ("homeandconstructionbusiness", "plumber", "electrician", "roofingcontractor", "hvacbusiness",
                       "generalcontractor", "housepainter", "locksmith", "movingcompany")),
    "real_estate": ("Real estate", "real estate agent", ("real estate", "realtor", "homes for sale", "listings",
                    "property management", "brokerage", "mls"), ("realestateagent",)),
    "restaurant": ("Restaurant / food", "restaurant", ("restaurant", "catering", "pizzeria", "cafe", "bakery",
                   "bistro", "takeout", "dine-in"), ("restaurant", "foodestablishment", "bakery", "cafeorcoffeeshop")),
    "beauty": ("Salon / spa", "salon", ("salon", "barber", "spa", "nail", "lash", "med spa", "massage", "hair"),
               ("beautysalon", "hairsalon", "dayspa", "nailsalon", "healthandbeautybusiness")),
    "fitness": ("Fitness", "gym", ("gym", "fitness", "personal training", "yoga", "pilates", "crossfit", "martial arts"),
                ("exercisegym", "sportsactivitylocation", "healthclub")),
    "auto": ("Automotive", "auto repair", ("auto repair", "mechanic", "dealership", "collision", "car wash",
             "auto body", "tires", "oil change"), ("autorepair", "autodealer", "autobodyshop", "automotivebusiness")),
    "ecommerce": ("Online store", "", ("add to cart", "shop now", "free shipping", "checkout", "shopping cart"),
                  ("store", "onlinestore")),
    "agency": ("Professional / B2B services", "", ("marketing agency", "digital marketing", "consulting", "accounting",
               "bookkeeping", "cpa", "software", "it services", "managed services", "staffing", "insurance agency"),
               ("professionalservice", "accountingservice", "insuranceagency", "financialservice")),
    "education": ("Education / childcare", "", ("daycare", "preschool", "child care", "tutoring", "academy",
                  "enroll", "school"), ("childcare", "preschool", "school", "educationalorganization")),
}

# Conversion paths per industry: (check id, severity, title when missing, detail, impact, keywords)
BOOKING_KW = ("calendly", "acuityscheduling", "zocdoc", "squareup.com/appointments", "booksy", "vagaro", "mindbody",
              "setmore", "localmed", "nexhealth", "jane.app", "simplybook", "fresha", "glossgenius", "schedulicity",
              "book online", "book now", "schedule online", "book an appointment", "request appointment",
              "request an appointment", "schedule an appointment", "book a visit", "schedule a visit")
PATHS = {
    "home_care": [
        ("no_care_request", "high", "No easy way to request care or a free assessment",
         "We found no 'request care', 'free in-home assessment' or 'care consultation' option on the site.",
         "Families looking for care are often in a hurry after a hospital stay. If requesting care isn't obvious, they call the next agency on Google.",
         ("free assessment", "in-home assessment", "free in-home", "care consultation", "request care", "request a consultation",
          "schedule a consultation", "get care", "start care", "request services", "care assessment", "free consultation",
          "request information", "request info", "get started")),
        ("no_caregiver_jobs", "medium", "No caregiver jobs or application page",
         "We found no careers, 'join our team' or caregiver application page.",
         "Home care agencies grow only as fast as they can hire caregivers. Without a careers page, job seekers go to agencies that make applying easy.",
         ("careers", "career", "join our team", "apply now", "employment", "caregiver jobs", "now hiring", "we're hiring",
          "job openings", "apply today", "work with us")),
        ("no_payment_info", "medium", "No information on Medicaid, insurance or how care is paid for",
         "The site doesn't say which payment options it accepts (Medicaid, long-term care insurance, VA, private pay or CDPAP).",
         "Payment is the first question most families have. If the site doesn't answer it, they call a competitor that does.",
         ("medicaid", "medicare", "insurance", "long-term care", "veterans", "va benefits", "private pay", "cdpap",
          "managed long term care", "mltc", "payment options")),
    ],
    "senior_living": [
        ("no_tour_request", "high", "No way to schedule a tour",
         "We found no 'schedule a tour' or 'visit us' option.",
         "Families decide after visiting. If booking a tour isn't easy, they tour somewhere else first.",
         ("schedule a tour", "book a tour", "tour", "visit us", "schedule a visit", "virtual tour")),
        ("no_payment_info", "medium", "No information on pricing, Medicaid or insurance",
         "The site doesn't explain costs or accepted payment (Medicaid, long-term care insurance, VA).",
         "Cost is the first question families ask; leaving it out sends them to sites that answer it.",
         ("medicaid", "insurance", "long-term care", "pricing", "cost", "veterans", "private pay")),
    ],
    "dental": [
        ("no_online_booking", "medium", "No way to book an appointment online",
         "Patients can't pick a time or request an appointment on the site.",
         "Many patients book outside office hours. If they can't book online, they book with a practice that lets them.",
         BOOKING_KW),
        ("no_insurance_info", "medium", "No list of insurance plans accepted",
         "We found no information about which dental insurance plans the practice accepts.",
         "'Do you take my insurance?' is the first question new patients ask. Without the answer, they pick a practice that shows it.",
         ("insurance", "ppo", "delta dental", "cigna", "aetna", "metlife", "guardian", "in-network", "financing")),
    ],
    "medical": [
        ("no_online_booking", "medium", "No way to book an appointment online",
         "Patients can't pick a time or request an appointment on the site.",
         "Patients increasingly expect to book online; practices without it lose new patients to those that offer it.",
         BOOKING_KW + ("patient portal", "request a visit")),
        ("no_insurance_info", "medium", "No list of insurance plans accepted",
         "We found no information about which insurance plans are accepted.",
         "Insurance is the first filter new patients use. Without it, they move on.",
         ("insurance", "in-network", "medicare", "medicaid", "aetna", "cigna", "united healthcare", "blue cross", "self-pay")),
    ],
    "legal": [
        ("no_case_evaluation", "high", "No free consultation or case evaluation offer",
         "We found no 'free consultation' or 'case evaluation' request.",
         "People with a legal problem contact the first firm that makes it easy and free to ask. Without that, they call someone else.",
         ("free consultation", "case evaluation", "case review", "free case", "schedule a consultation", "contact us today",
          "consultation")),
    ],
    "home_services": [
        ("no_quote_request", "high", "No 'get a quote' or 'request service' form",
         "We found no quote, estimate or service-request option.",
         "Homeowners collect 2-3 quotes. If yours isn't one click away, you're not in the running.",
         ("quote", "estimate", "request service", "schedule service", "book service", "service request", "book now",
          "schedule online")),
        ("no_emergency_info", "low", "No emergency or same-day service information",
         "The site doesn't say whether you offer emergency, 24/7 or same-day service.",
         "Urgent jobs are the most valuable leads, and those customers call whoever says they can come today.",
         ("emergency", "24/7", "24 hours", "same-day", "same day", "after hours")),
    ],
    "real_estate": [
        ("no_home_valuation", "medium", "No home valuation offer for sellers",
         "We found no 'what's my home worth' or valuation request.",
         "Valuation requests are the main way agents capture sellers online; without one, sellers go to Zillow.",
         ("home value", "home worth", "valuation", "market analysis", "cma", "what's my home")),
        ("no_listing_search", "medium", "No property search or listings",
         "We found no IDX/MLS search or listings on the site.",
         "Buyers stay on sites where they can search homes; without listings they leave for portals.",
         ("idx", "listings", "property search", "search homes", "featured properties", "mls", "homes for sale")),
    ],
    "restaurant": [
        ("no_order_or_reserve", "high", "No online ordering or reservations",
         "We found no link to order online or reserve a table.",
         "Hungry customers order from whoever makes it a two-tap job.",
         ("order online", "order now", "doordash", "ubereats", "grubhub", "toasttab", "chownow", "slice", "opentable",
          "resy", "reservations", "reserve", "sevenrooms", "tock")),
        ("menu_pdf_only", "medium", "Menu is only a PDF or image",
         "The menu isn't readable text on the page.",
         "PDF menus are slow on phones and invisible to Google searches for dishes.",
         None),
    ],
    "beauty": [
        ("no_online_booking", "high", "No way to book online",
         "Clients can't pick a service and time on the site.",
         "Most salon and spa clients book on their phone, often at night. Without online booking they book elsewhere.",
         BOOKING_KW),
    ],
    "fitness": [
        ("no_trial_signup", "high", "No free trial, class booking or membership sign-up",
         "We found no way to start a trial, book a class or join online.",
         "People decide to start in a moment of motivation; if they can't sign up right then, many never do.",
         BOOKING_KW + ("free trial", "free class", "join now", "sign up", "membership", "schedule", "first class free")),
    ],
    "auto": [
        ("no_service_booking", "medium", "No way to schedule service online",
         "Customers can't request an appointment or service online.",
         "Drivers book with the shop that lets them pick a time without calling.",
         BOOKING_KW + ("schedule service", "request service", "service appointment", "get a quote", "estimate")),
    ],
    "agency": [
        ("no_consult_booking", "medium", "No way to book a call or consultation",
         "We found no 'book a call', 'free consultation' or scheduling link.",
         "B2B buyers want to talk before they buy; a booking link turns interest into a meeting without back-and-forth.",
         BOOKING_KW + ("book a call", "strategy call", "free consultation", "schedule a call", "book a demo",
                       "request a demo", "free audit", "get a proposal", "contact us")),
    ],
    "education": [
        ("no_tour_or_enroll", "high", "No way to schedule a tour or start enrollment",
         "We found no tour request, enrollment form or waitlist.",
         "Parents compare a few options; the ones that make touring easy get the visit.",
         ("schedule a tour", "book a tour", "enroll", "enrollment", "waitlist", "apply", "admissions", "register")),
    ],
}

# Wording of common findings that fits the industry better than the generic line.
IMPACT = {
    "home_care": {
        "no_reviews": "Families choosing a caregiver for a parent read reviews first; without them, trust goes to agencies that show them.",
        "no_verified_reviews": "Families trust reviews they can check on Google far more than quotes on your own site.",
        "no_trust_badges": "Families need to see you're licensed, insured and that caregivers are background-checked before they call.",
        "no_live_chat": "Adult children researching care late at night often prefer to message rather than call.",
        "no_cta_first_screen_mobile": "Families often search on a phone right after a hospital visit; if 'request care' isn't visible, they call the next agency.",
    },
    "senior_living": {"no_trust_badges": "Families need to see licensing, inspections and awards before they visit."},
    "legal": {"no_trust_badges": "Clients look for bar membership, results and awards before trusting a firm."},
    "dental": {"no_reviews": "Most new patients read reviews before choosing a dentist."},
}

TRUST_KW = {
    "home_care": ("licensed", "background-checked", "background checked", "bonded", "insured", "chap", "joint commission",
                  "accredited", "certified", "department of health", "nys doh", "trained caregivers"),
    "senior_living": ("licensed", "accredited", "inspection", "award", "certified"),
}


def detect(lead: dict, home_text: str, title_h1: str, jsonld_types: list[str]) -> dict:
    """Returns {"key", "label", "search_term", "source"}. Lead form wins, then schema, then the site's own words."""
    def from_text(t: str):
        t = t.lower()
        best, score = None, 0
        for k, (_, _, kws, _) in INDUSTRIES.items():
            s = sum(len(re.findall(rf"\b{re.escape(w)}", t)) for w in kws)  # word start: "spa" != "space"
            if s > score:
                best, score = k, s
        return best, score

    ind = (lead.get("industry") or lead.get("category") or "").strip()
    if ind:
        k, s = from_text(ind)
        if k:
            return _out(k, "lead form", ind)
    types = {t.lower() for t in jsonld_types}
    for k, (*_, schema) in INDUSTRIES.items():
        if types & set(schema):
            return _out(k, "structured data")
    k, s = from_text(title_h1 * 3 + " " + home_text[:20000])  # title/H1 count triple
    if k and s >= 3:
        return _out(k, "site content")
    return {"key": "general", "label": "General business", "search_term": "", "source": "none"}


def _out(k, source, raw=""):
    label, term, *_ = INDUSTRIES[k]
    return {"key": k, "label": label, "search_term": raw.lower() if raw and source == "lead form" else term, "source": source}


def checks(ind: dict, all_html: str, soups, add) -> None:
    """Industry-specific conversion checks. A missing path is only reported when no keyword for it appears anywhere."""
    for fid, sev, title, detail, impact, kws in PATHS.get(ind["key"], []):
        if fid == "menu_pdf_only":
            menu_links = [a.get("href", "") for _, s in soups for a in s.find_all("a", href=True)
                          if re.search(r"menu", (a.get_text(" ") + a.get("href", "")), re.I)]
            if menu_links and all(re.search(r"\.(pdf|jpe?g|png)(\?|$)", h, re.I) for h in menu_links):
                add("conversion", fid, sev, title, detail, "Put the menu on the page as text.", menu_links, impact=impact)
            continue
        if not any(k in all_html for k in kws):
            add("conversion", fid, sev, title, detail, "Add a clear path for this on every page.", impact=impact)


def trust_keywords(key: str) -> tuple:
    return TRUST_KW.get(key, ())


def action_words(key: str) -> str:
    return {"home_care": "'request care' or 'free assessment'", "senior_living": "'schedule a tour'",
            "dental": "'book an appointment'", "medical": "'book an appointment'", "legal": "'free consultation'",
            "home_services": "'get a quote'", "real_estate": "'search homes' or 'home value'", "restaurant": "'order' or 'reserve'",
            "beauty": "'book now'", "fitness": "'free trial' or 'join'", "auto": "'schedule service'",
            "agency": "'book a call'", "education": "'schedule a tour'"}.get(key, "'contact us' or 'get a quote'")


PATH_LABELS = {
    "no_care_request": "Easy way to request care or an assessment", "no_caregiver_jobs": "Caregiver jobs page",
    "no_payment_info": "Payment, Medicaid and insurance info", "no_tour_request": "Schedule a tour online",
    "no_online_booking": "Online booking", "no_insurance_info": "Insurance plans listed",
    "no_case_evaluation": "Free consultation offer", "no_quote_request": "Quote or service request form",
    "no_emergency_info": "Emergency / same-day info", "no_home_valuation": "Home valuation offer",
    "no_listing_search": "Property search", "no_order_or_reserve": "Order online or reserve",
    "menu_pdf_only": "Menu readable on the page", "no_trial_signup": "Trial, class or membership sign-up",
    "no_service_booking": "Schedule service online", "no_consult_booking": "Book a call online",
    "no_tour_or_enroll": "Tour or enrollment request",
}


def checklist_rows(key: str) -> list[tuple]:
    return [(p[0], PATH_LABELS.get(p[0], p[2]), None) for p in PATHS.get(key, [])]
