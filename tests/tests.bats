#!/usr/bin/env bats

@test "AWS CLI" {
  v="$(aws --version 2>&1)"
  [[ "$v" =~ "aws-cli" ]]
}

@test "Curl v7.47.0" {
  v="$(curl --version)"
  [[ "$v" =~ "7.47.0" ]]
}

@test "Make sure the run script is in the PATH" {
  h="$(run_sortmerna.py -h 2>&1)"
  
  [[ "$h" =~ "SortMeRNA" ]]
}
