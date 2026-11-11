#!/bin/sh
# Zet de site in één keer terug naar de live versie van vóór het redesign (tag v1-donker-live).
# Gebruik:  sh .ops/restore-v1.sh          (maakt alleen een commit op main; pushen doe je zelf)
#           BRANCH=redesign sh .ops/restore-v1.sh   (om het op een andere branch te testen)
# Let op: een push naar main deployt direct naar de live site.
set -e
cd "$(dirname "$0")/.."
BRANCH="${BRANCH:-main}"
git fetch --tags -q
git switch "$BRANCH"
# 1. alle bestanden zoals ze in v1 waren
git checkout v1-donker-live -- .
# 2. bestanden die sindsdien zijn toegevoegd weer weghalen uit de repo
git diff --name-only --diff-filter=A -z v1-donker-live HEAD | xargs -0 -r git rm -q -f --
git commit -q -m "Terug naar de donkere versie (v1-donker-live)" || echo "Niets te herstellen: branch staat al op v1."
echo "Klaar. Controleer met:  git show --stat HEAD"
echo "Live zetten met:        git push origin $BRANCH   (deployt direct)"
echo "Let op: de server verwijdert geen bestanden; nieuwe pagina's blijven daar staan maar zijn niet meer gelinkt."
