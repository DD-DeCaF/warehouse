#!/usr/bin/env bash
PATTERN="Novo Nordisk Foundation Center for Biosustainability"
RET=0
for file in $(find $@ -name '*.py')
do
  grep "${PATTERN}" ${file} >/dev/null
  if [[ $? != 0 ]]
  then
    echo "Source code file ${file} seems to be missing a license header"
    RET=1
  fi
done
exit ${RET}
