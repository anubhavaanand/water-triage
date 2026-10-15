"""
Canonical district name registry for Uttar Pradesh (75) and Bihar (38).

These are the official Census 2011 administrative districts. Used to filter
WQ6 extraction output so that state-level aggregate rows and out-of-state
districts (file 9 is a national summary) are excluded.

Names are normalized by normalize_district() (title-cased, no parentheticals,
collapsed whitespace). The keys below are the post-normalization form so they
match the cleaned district column directly.
"""

UP_DISTRICTS = {
    'Agra', 'Aligarh', 'Ambedkar Nagar', 'Amethi', 'Amroha', 'Auraiya',
    'Ayodhya', 'Azamgarh', 'Baghpat', 'Bahraich', 'Ballia', 'Balrampur',
    'Banda', 'Bara Banki', 'Bareilly', 'Basti', 'Bhadohi', 'Bijnor',
    'Budaun', 'Bulandshahr', 'Chandauli', 'Chitrakoot', 'Deoria', 'Etah',
    'Etawah', 'Farrukhabad', 'Fatehpur', 'Firozabad', 'Gautam Buddha Nagar',
    'Ghaziabad', 'Ghazipur', 'Gonda', 'Gorakhpur', 'Hamirpur', 'Hapur',
    'Hardoi', 'Hathras', 'Jalaun', 'Jaunpur', 'Jhansi', 'Kannauj',
    'Kanpur Dehat', 'Kanpur Nagar', 'Kasganj', 'Kaushambi', 'Kheri',
    'Kushinagar', 'Lalitpur', 'Lucknow', 'Mahoba', 'Mahrajganj',
    'Mainpuri', 'Mau', 'Mathura', 'Meerut', 'Mirzapur', 'Moradabad', 'Muzaffarnagar',
    'Pilibhit', 'Pratapgarh', 'Prayagraj', 'Rae Bareli', 'Rampur',
    'Saharanpur', 'Sant Kabir Nagar', 'Sambhal',
    'Sitapur', 'Sonbhadra', 'Sultanpur', 'Shahjahanpur', 'Shrawasti',
    'Shamli', 'Siddharthnagar', 'Unnao', 'Varanasi',
}

BIHAR_DISTRICTS = {
    'Araria', 'Arwal', 'Aurangabad', 'Banka', 'Begusarai', 'Bhagalpur',
    'Bhojpur', 'Buxar', 'Darbhanga', 'Gaya', 'Gopalganj', 'Jamui',
    'Jehanabad', 'Kaimur (Bhabua)', 'Katihar', 'Khagaria', 'Kishanganj',
    'Lakhisarai', 'Madhepura', 'Madhubani', 'Munger', 'Muzaffarpur',
    'Nalanda', 'Nawada', 'Patna', 'Purnia', 'Rohtas', 'Saharsa',
    'Samastipur', 'Saran', 'Sheikhpura', 'Sheohar', 'Sitamarhi', 'Siwan',
    'Supaul', 'Vaishali', 'Pashchim Champaran', 'Purbi Champaran',
}

CANONICAL_DISTRICTS = {
    'Uttar Pradesh': UP_DISTRICTS,
    'Bihar': BIHAR_DISTRICTS,
}
