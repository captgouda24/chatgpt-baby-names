You are coding NASA ASRS reports filed by airline crew about passenger misconduct. Each report has an ACN (id), a synopsis and one or two narratives. Read the whole text of each report and code what the reporter says happened. Judge only from the text; do not assume details that are not stated.

Fields (all 0/1 unless noted):

- violent: a passenger did at least one of the following:
  - used physical force against a person: hit, punched, slapped, kicked, bit, choked, shoved, pushed, grabbed, spat on, threw an object at, or otherwise assaulted someone
  - had to be physically restrained: restraint kit, flex cuffs, duct tape, held down, tackled, subdued by crew or passengers
  - tried to open a door or emergency exit in flight, or tried to enter the cockpit by force
  - groped or sexually assaulted someone (physical contact)
  - made a threat to kill or seriously harm someone, a bomb threat, or a hijack threat

  Verbal abuse, yelling, profanity, refusing instructions, intoxication, or physical contact only with objects (e.g. slamming a bin) are NOT violent unless one of the above also happened.
- restrained: the passenger was physically restrained (restraint kit, cuffs, tape, held down).
- threat: the passenger made a threat to kill or harm, or a bomb or hijack threat.
- crew_assaulted: a crew member was physically struck, pushed, grabbed or injured by a passenger.
- mask: the conflict involved masks or face coverings.
- alcohol: the passenger was described as intoxicated or drinking, or alcohol was a factor.
- diverted: the flight diverted, returned to the gate, or returned to the departure airport because of the passenger.
- police: law enforcement met the flight or removed or arrested the passenger.
- us: 1 if the flight was a US carrier or to, from or within the US; 0 if clearly not; ? if unclear.

Output: one line per report, tab-separated, in this order:

ACN<TAB>violent<TAB>restrained<TAB>threat<TAB>crew_assaulted<TAB>mask<TAB>alcohol<TAB>diverted<TAB>police<TAB>us

No header and no commentary. Every ACN must appear exactly once.
