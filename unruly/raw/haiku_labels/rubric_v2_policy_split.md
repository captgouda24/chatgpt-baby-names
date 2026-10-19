These headlines were all labeled as general (not single-incident) stories about airline passengers. Split them into two groups, judging from the headline text alone.

- misconduct: the story is about passenger misbehavior or its consequences. This includes:
  - statistics or trends in unruly or disruptive passengers
  - fines, referrals, prosecutions or bans for passengers who misbehave, including passengers banned or fined for refusing masks
  - laws, bills or no-fly lists aimed at unruly passengers
  - unions, crews or airlines talking about passenger behavior, violence or abuse; crew self-defense training
  - alcohol restrictions explicitly justified by unruly behavior
  - explainers or opinion about why passengers misbehave
- health_rule: the story announces, explains or debates a rule or service change without a misconduct angle. This includes:
  - airlines or governments requiring masks, testing or vaccination
  - suspending food or alcohol service because of COVID
  - extending or ending mask mandates
  - distancing or blocked middle seats
  - general travel-safety advice
- other: neither (e.g. general airline business news).

If a headline mentions both a rule and its enforcement against passengers who break it (e.g. "Airlines will ban passengers who refuse masks"), use misconduct.

Output: one line per input headline, tab-separated: id<TAB>group. No header and no commentary. Every id must appear exactly once.
