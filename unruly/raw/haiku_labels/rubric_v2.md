You are labeling news headlines found by a broad keyword filter (a misconduct word plus a passenger/crew/flight word). Many are NOT about airline passenger misconduct. Judge each headline from its text alone.

The headlines in one file all come from the same calendar month, sorted by date.

## kind (exactly one)

- aggregate_or_policy: about airline passenger misconduct in general, not one specific incident. Statistics or trends ("incidents soar", "FAA has received 3,000 reports"), FAA fines or referrals announced in aggregate ("FAA proposes $500K in fines against 10 passengers"), laws, bills, no-fly-list proposals, unions, airline or airport policies on alcohol or behavior, explainers, opinion pieces.
- incident_violent: one specific incident in which a passenger (or a group of passengers) is alleged to have:
  - used physical force against a person: hitting, punching, biting, kicking, choking, shoving, spitting on someone, or repeatedly punching an occupied seat
  - been physically restrained: duct-taped, zip-tied, handcuffed on board, subdued, tackled
  - tried to open a door or emergency exit in flight, or tried to breach or storm the cockpit
  - committed groping or sexual assault (physical contact)
  - made threats to kill, a bomb threat, or a hijack threat
- incident_nonviolent: one specific incident in which a passenger is alleged to have misbehaved without any of the above: refusing a mask or other crew instructions, yelling, verbal abuse, racist or abusive rants, intoxication, smoking or vaping, indecent exposure or a lewd act without contact, a false claim (e.g. of having COVID), causing a diversion or being removed or arrested for disruptive behavior. Fines, charges, pleas or sentences for one person's specific incident belong here or in incident_violent, depending on what they did.
- other: everything else. This includes:
  - crashes, weather, mechanical diversions, medical emergencies
  - misconduct by pilots, crew or airline staff (unless they are victims of a passenger)
  - an airline removing or refusing passengers where the story alleges no passenger misbehavior (e.g. alleged discrimination, body odor, dress code, overbooking)
  - smuggling, drugs, weapons in luggage, abandoned pets, lost luggage, customs
  - incidents in cars, taxis, Uber, buses, trains, ships or cruises
  - general crime that merely mentions a flight or traveler
  - headlines too vague to tell

If a specific incident mentions any violent element listed above, use incident_violent.

## mask

1 if the headline mentions masks or face coverings, else 0.

## us

- 1: the flight or incident involves a US airline, or a flight to, from or within the US; for aggregate_or_policy, the story is about the US (FAA, Congress, US airlines or unions).
- 0: clearly elsewhere (e.g. Indian, Australian, European or Canadian domestic flights or regulators).
- ?: cannot tell.

For kind = other, put -.

## event

For incident_violent and incident_nonviolent, give every headline about the same specific incident the same short event code within this file: E1, E2, E3, ... Many outlets rewrite the same story, so group headlines that clearly describe the same incident (same airline or route, same act, similar date), even if the wording differs. A later headline about the same person's arrest, charge or sentence is the same event. Use a new code for each distinct incident.

For aggregate_or_policy and other, put -.

## Output

One line per input headline, tab-separated:

id<TAB>kind<TAB>mask<TAB>us<TAB>event

No header and no commentary. Every id must appear exactly once.
