You are labeling US news headlines that matched the phrase "unruly passenger(s)". Label each headline from its text alone.

kind (exactly one):
- aggregate_or_policy: not about one specific incident. Statistics or trend stories ("incidents soar", "FAA has received 3,000 reports"), FAA fines or enforcement announced in aggregate (e.g. "FAA proposes $500K in fines against 10 passengers"), laws, bills, no-fly-list proposals, unions, airline campaigns, alcohol policy, explainers and opinion.
- incident_violent: one specific incident involving physical violence (punching, hitting, biting, kicking, choking, assaulting crew or passengers), being physically restrained (duct-taped, zip-tied, subdued, tackled), trying to open a door/emergency exit or breach the cockpit, sexual assault/groping, or threats to kill / bomb threats.
- incident_nonviolent: one specific incident without any of the above: mask refusal, yelling, verbal abuse, intoxication, smoking, a diversion or removal from a flight, arrest or charges where no violence is indicated.
- other: not about airline passenger misconduct (sports, politics using the phrase metaphorically, bus/train/cruise, unrelated).

A headline about a single person's fine, charge or sentencing for a specific incident is an incident (violent or not depending on what they did). If violence is mentioned at all for a specific incident, use incident_violent.

mask: 1 if the headline mentions masks/face coverings, else 0.

Output: one line per input headline, tab-separated: id<TAB>kind<TAB>mask. No header, no commentary, every id exactly once.
