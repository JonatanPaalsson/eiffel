#!/usr/bin/env python

# Copyright 2017 Ericsson AB.
# For a full list of individual contributors, please see the commit history.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import uuid
import time
import getopt
import sys
import random

def generateGenericMeta(type, t, v):
  return {"type": type, "id": str(uuid.uuid4()), "time": t, "source": {"domainId": "example.domain"}, "version": v}

def link(source, target, type):
  if not target:
    return None

  source["links"].append({"type": type, "target": target["meta"]["id"]})

def generateGenericMessage(type, t, v, name, iteration):
  meta = generateGenericMeta(type, t, v)
  data = {"customData": [{"key": "name", "value": name}, {"key": "iteration", "value": iteration}]}
  links = []
  msg = {}
  msg["meta"] = meta
  msg["data"] = data
  msg["links"] = links
  return msg

def findLatestPrevious(iterationsMap, currentIteration, name):
  for it in range(currentIteration - 1, -1, -1):
    if it in iterationsMap:
      if name in iterationsMap[it]:
        return iterationsMap[it][name]

def randomizeVerdict(chanceOfSuccess):
  if random.random() < chanceOfSuccess:
    return "PASSED"
  else:
    return "FAILED"

def getOutcomeValuesFromVerdicts(testCaseFinishedEventsArray, positiveName, negativeName):
  for tcfEvent in testCaseFinishedEventsArray:
    if tcfEvent["data"]["outcome"]["verdict"] != "PASSED":
      return negativeName

  return positiveName

def generateSCC1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelSourceChangeCreatedEvent", t+timeToAdd, "1.0.0", "SCC1", iteration)
  link(msg, findLatestPrevious(iterationsMap, iteration, "SCS1"), "BASE")

  msg["data"]["gitIdentifier"] = {"commitId": "fd090b60a4aedc5161da9c035a49b14a319829c5", "branch": "topic-branch-" + str(iteration), "repoName": "myRepo", "repoUri": "https://repo.com"}
  msg["data"]["author"] = {"name": "John Doe", "email": "john.doe@company.com", "id": "johnxxx", "group": "Team Gophers"}
  msg["data"]["change"] = {"files": "https://filelist.com/" + str(iteration), "insertions": random.randint(10, 500), "deletions": random.randint(10, 500)}

  return msg

def generateSCS1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelSourceChangeSubmittedEvent", t+timeToAdd, "1.0.0", "SCS1", iteration)
  link(msg, findLatestPrevious(iterationsMap, iteration, "SCS1"), "PREVIOUS_VERSION")
  if "SCC1" in iterationsMap[iteration]:
    link(msg, iterationsMap[iteration]["SCC1"], "CHANGE")

  msg["data"]["gitIdentifier"] = {"commitId": "fd090b60a4aedc5161da9c035a49b14a319829b4", "branch": "master", "repoName": "myRepo", "repoUri": "https://repo.com"}
  msg["data"]["submitter"] = {"name": "John Doe", "email": "john.doe@company.com", "id": "johnxxx", "group": "Team Gophers"}

  return msg

def generateEDef1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelEnvironmentDefinedEvent", t+timeToAdd, "1.0.0", "EDef1", iteration)
  msg["data"]["name"] = "Environment 1"
  msg["data"]["version"] = str(iteration)
  return msg

def generateEDef2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelEnvironmentDefinedEvent", t+timeToAdd, "1.0.0", "EDef2", iteration)
  msg["data"]["name"] = "Environment 2"
  msg["data"]["version"] = str(iteration)
  return msg

def generateArtC3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactCreatedEvent", t+timeToAdd, "1.0.0", "ArtC3", iteration)
  msg["data"]["gav"] = {"groupId": "com.othercompany.library", "artifactId": "third-party-library", "version": "3.2.4"}
  msg["data"]["fileInformation"] = [{"classifier": "", "extension": "jar"}]
  return msg

def generateCDef1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelCompositionDefinedEvent", t+timeToAdd, "1.0.0", "CDef1", iteration)
  msg["data"]["name"] = "Composition 1"
  msg["data"]["version"] = str(iteration)
  link(msg, findLatestPrevious(iterationsMap, iteration, "CDef1"), "PREVIOUS_VERSION")
  link(msg, iterationsMap[iteration]["CLM2"], "CAUSE")
  link(msg, iterationsMap[iteration]["ArtC2"], "ELEMENT")
  link(msg, iterationsMap[0]["ArtC3"], "ELEMENT")
  return msg

def generateCDef2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelCompositionDefinedEvent", t+timeToAdd, "1.0.0", "CDef2", iteration)
  msg["data"]["name"] = "Composition 2"
  msg["data"]["version"] = str(iteration)
  link(msg, findLatestPrevious(iterationsMap, iteration, "CDef2"), "PREVIOUS_VERSION")
  link(msg, iterationsMap[iteration]["ActT4"], "CONTEXT")
  link(msg, findLatestPrevious(iterationsMap, iteration + 1, "ArtCC1"), "ELEMENT")
  link(msg, findLatestPrevious(iterationsMap, iteration + 1, "ArtCC2"), "ELEMENT")
  link(msg, findLatestPrevious(iterationsMap, iteration + 1, "ArtCC3"), "ELEMENT")
  return msg

def generateCDef3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelCompositionDefinedEvent", t+timeToAdd, "1.0.0", "CDef3", iteration)
  msg["data"]["name"] = "Composition 3"
  msg["data"]["version"] = str(iteration)
  link(msg, findLatestPrevious(iterationsMap, iteration, "CDef3"), "PREVIOUS_VERSION")
  link(msg, iterationsMap[iteration]["SCS1"], "ELEMENT")
  return msg

def generateArtC1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactCreatedEvent", t+timeToAdd, "1.0.0", "ArtC1", iteration)
  link(msg, iterationsMap[iteration]["CDef1"], "COMPOSITION")
  link(msg, iterationsMap[0]["EDef1"], "ENVIRONMENT")
  link(msg, iterationsMap[iteration]["CDef1"], "CAUSE")
  link(msg, findLatestPrevious(iterationsMap, iteration, "ArtC1"), "PREVIOUS_VERSION")
  msg["data"]["gav"] = {"groupId": "com.mycompany.myproduct", "artifactId": "complete-system", "version": "1." + str(iteration) + ".0"}
  msg["data"]["fileInformation"] = [{"classifier": "", "extension": "jar"}]
  return msg

def generateArtC2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactCreatedEvent", t+timeToAdd, "1.0.0", "ArtC2", iteration)
  link(msg, iterationsMap[iteration]["CDef2"], "COMPOSITION")
  link(msg, iterationsMap[0]["EDef2"], "ENVIRONMENT")
  link(msg, findLatestPrevious(iterationsMap, iteration, "ArtC2"), "PREVIOUS_VERSION")
  link(msg, iterationsMap[iteration]["ActT4"], "CONTEXT")
  msg["data"]["gav"] = {"groupId": "com.mycompany.myproduct", "artifactId": "sub-system", "version": "1." + str(iteration) + ".0"}
  msg["data"]["fileInformation"] = [{"classifier": "", "extension": "jar"}]
  return msg

def generateArtCC1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactCreatedEvent", t+timeToAdd, "1.0.0", "ArtCC1", iteration)
  link(msg, iterationsMap[iteration]["CDef3"], "COMPOSITION")
  link(msg, iterationsMap[iteration]["CDef3"], "CAUSE")
  link(msg, findLatestPrevious(iterationsMap, iteration, "ArtCC1"), "PREVIOUS_VERSION")
  msg["data"]["gav"] = {"groupId": "com.mycompany.myproduct", "artifactId": "component-1", "version": "1." + str(iteration) + ".0"}
  msg["data"]["fileInformation"] = [{"classifier": "", "extension": "jar"}]
  return msg

def generateArtCC2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactCreatedEvent", t+timeToAdd, "1.0.0", "ArtCC2", iteration)
  link(msg, iterationsMap[iteration]["CDef3"], "COMPOSITION")
  link(msg, iterationsMap[iteration]["CDef3"], "CAUSE")
  link(msg, findLatestPrevious(iterationsMap, iteration, "ArtCC2"), "PREVIOUS_VERSION")
  msg["data"]["gav"] = {"groupId": "com.mycompany.myproduct", "artifactId": "component-2", "version": "1." + str(iteration) + ".0"}
  msg["data"]["fileInformation"] = [{"classifier": "", "extension": "jar"}]
  return msg

def generateArtCC3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactCreatedEvent", t+timeToAdd, "1.0.0", "ArtCC3", iteration)
  link(msg, iterationsMap[iteration]["CDef3"], "COMPOSITION")
  link(msg, iterationsMap[iteration]["CDef3"], "CAUSE")
  link(msg, findLatestPrevious(iterationsMap, iteration, "ArtCC3"), "PREVIOUS_VERSION")
  msg["data"]["gav"] = {"groupId": "com.mycompany.myproduct", "artifactId": "component-3", "version": "1." + str(iteration) + ".0"}
  msg["data"]["fileInformation"] = [{"classifier": "", "extension": "jar"}]
  return msg

def generateArtP1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactPublishedEvent", t+timeToAdd, "1.0.0", "ArtP1", iteration)
  link(msg, iterationsMap[iteration]["ArtC1"], "ARTIFACT")
  link(msg, iterationsMap[iteration]["ArtC1"], "CAUSE")
  msg["data"]["locations"] =  [{"type": "PLAIN", "uri": "https://myrepository.com/myCompleteSystemArtifact"}]
  return msg

def generateArtP2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelArtifactPublishedEvent", t+timeToAdd, "1.0.0", "ArtP2", iteration)
  link(msg, iterationsMap[iteration]["ArtC2"], "ARTIFACT")
  link(msg, iterationsMap[iteration]["ActT4"], "CONTEXT")
  msg["data"]["locations"] =  [{"type": "PLAIN", "uri": "https://myrepository.com/mySubSystemArtifact"}]
  return msg

def generateActT3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityTriggeredEvent", t+timeToAdd, "1.0.0", "ActT3", iteration)
  link(msg, iterationsMap[iteration]["ArtP2"], "CAUSE")
  msg["data"]["name"] = "Act3"
  msg["data"]["categories"] = ["Sub-system Test Activity"]
  msg["data"]["triggers"] = [ {"type": "EIFFEL_EVENT"} ]
  msg["data"]["executionType"] = "AUTOMATED"
  return msg

def generateActS3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityStartedEvent", t+timeToAdd, "1.0.0", "ActS3", iteration)
  link(msg, iterationsMap[iteration]["ActT3"], "ACTIVITY_EXECUTION")
  return msg

def generateActF3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityFinishedEvent", t+timeToAdd, "1.0.0", "ActF3", iteration)
  link(msg, iterationsMap[iteration]["ActT3"], "ACTIVITY_EXECUTION")
  msg["data"]["outcome"] = {"conclusion": getOutcomeValuesFromVerdicts([iterationsMap[iteration]["TSF1"]], "SUCCESSFUL", "UNSUCCESSFUL")}

  return msg

def generateActT4(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityTriggeredEvent", t+timeToAdd, "1.0.0", "ActT4", iteration)
  if "ArtCC1" in iterationsMap[iteration]:
    link(msg,  iterationsMap[iteration]["ArtCC1"], "CAUSE")
  if "ArtCC2" in iterationsMap[iteration]:
    link(msg,  iterationsMap[iteration]["ArtCC2"], "CAUSE")
  if "ArtCC3" in iterationsMap[iteration]:
    link(msg,  iterationsMap[iteration]["ArtCC3"], "CAUSE")
  msg["data"]["name"] = "Act4"
  msg["data"]["categories"] = ["Sub-system Build Activity"]
  msg["data"]["triggers"] = [ {"type": "EIFFEL_EVENT"} ]
  msg["data"]["executionType"] = "AUTOMATED"
  return msg

def generateActS4(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityStartedEvent", t+timeToAdd, "1.0.0", "ActS4", iteration)
  link(msg, iterationsMap[iteration]["ActT4"], "ACTIVITY_EXECUTION")
  return msg

def generateActF4(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityFinishedEvent", t+timeToAdd, "1.0.0", "ActF4", iteration)
  link(msg, iterationsMap[iteration]["ActT4"], "ACTIVITY_EXECUTION")
  if "ArtC2" in iterationsMap[iteration]:
    msg["data"]["outcome"] = {"conclusion": "SUCCESSFUL"}
  else:
    msg["data"]["outcome"] = {"conclusion": "UNSUCCESSFUL"}

  return msg

def generateActT1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityTriggeredEvent", t+timeToAdd, "1.0.0", "ActT1", iteration)
  link(msg, iterationsMap[iteration]["ArtP1"], "CAUSE")
  msg["data"]["name"] = "Act1"
  msg["data"]["categories"] = ["Test Activity"]
  msg["data"]["triggers"] = [ {"type": "EIFFEL_EVENT"} ]
  msg["data"]["executionType"] = "AUTOMATED"
  return msg

def generateActS1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityStartedEvent", t+timeToAdd, "1.0.0", "ActS1", iteration)
  link(msg, iterationsMap[iteration]["ActT1"], "ACTIVITY_EXECUTION")
  return msg

def generateActF1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityFinishedEvent", t+timeToAdd, "1.0.0", "ActF1", iteration)
  link(msg, iterationsMap[iteration]["ActT1"], "ACTIVITY_EXECUTION")
  msg["data"]["outcome"] = {"conclusion": getOutcomeValuesFromVerdicts([iterationsMap[iteration]["TCF1"], iterationsMap[iteration]["TCF2"]], "SUCCESSFUL", "UNSUCCESSFUL")}

  return msg

def generateTCT1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT1", iteration)
  msg["data"]["testCase"] = {"tracker": "My First Test Management System", "id": "TC1", "uri": "http://tm.company.com/browse/TC1"}
  link(msg, iterationsMap[iteration]["ActT1"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC1"], "IUT")
  return msg

def generateTCS1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS1", iteration)
  link(msg, iterationsMap[iteration]["TCT1"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF1", iteration)
  link(msg, iterationsMap[iteration]["TCT1"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.95), "conclusion": "SUCCESSFUL"}
  return msg

def generateTCT2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT2", iteration)
  msg["data"]["testCase"] = {"tracker": "My First Test Management System", "id": "TC2", "uri": "http://tm.company.com/browse/TC2"}
  link(msg, iterationsMap[iteration]["ActT1"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC1"], "IUT")
  return msg

def generateTCS2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS2", iteration)
  link(msg, iterationsMap[iteration]["TCT2"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF2", iteration)
  link(msg, iterationsMap[iteration]["TCT2"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.95), "conclusion": "SUCCESSFUL"}
  return msg

def generateActT2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityTriggeredEvent", t+timeToAdd, "1.0.0", "ActT2", iteration)
  link(msg, iterationsMap[iteration]["ArtP1"], "CAUSE")
  msg["data"]["name"] = "Act2"
  msg["data"]["categories"] = ["Test Activity"]
  msg["data"]["triggers"] = [ {"type": "EIFFEL_EVENT"} ]
  msg["data"]["executionType"] = "AUTOMATED"
  return msg

def generateActS2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityStartedEvent", t+timeToAdd, "1.0.0", "ActS2", iteration)
  link(msg, iterationsMap[iteration]["ActT2"], "ACTIVITY_EXECUTION")
  return msg

def generateActF2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelActivityFinishedEvent", t+timeToAdd, "1.0.0", "ActF2", iteration)
  link(msg, iterationsMap[iteration]["ActT2"], "ACTIVITY_EXECUTION")
  msg["data"]["outcome"] = {"conclusion": getOutcomeValuesFromVerdicts([iterationsMap[iteration]["TCF3"], iterationsMap[iteration]["TCF4"]], "SUCCESSFUL", "UNSUCCESSFUL")}
  return msg

def generateTCT3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT3", iteration)
  msg["data"]["testCase"] = {"tracker": "My First Test Management System", "id": "TC3", "uri": "http://tm.company.com/browse/TC3"}
  link(msg, iterationsMap[iteration]["ActT2"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC1"], "IUT")
  return msg

def generateTCS3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS3", iteration)
  link(msg, iterationsMap[iteration]["TCT3"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF3(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF3", iteration)
  link(msg, iterationsMap[iteration]["TCT3"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.99), "conclusion": "SUCCESSFUL"}
  return msg

def generateTCT4(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT4", iteration)
  msg["data"]["testCase"] = {"tracker": "My First Test Management System", "id": "TC4", "uri": "http://tm.company.com/browse/TC4"}
  link(msg, iterationsMap[iteration]["ActT2"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC1"], "IUT")
  return msg

def generateTCS4(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS4", iteration)
  link(msg, iterationsMap[iteration]["TCT4"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF4(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF4", iteration)
  link(msg, iterationsMap[iteration]["TCT4"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.90), "conclusion": "SUCCESSFUL"}
  return msg

def generateTCT5(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT5", iteration)
  msg["data"]["testCase"] = {"tracker": "My Other Test Management System", "id": "TC5", "uri": "https://other-tm.company.com/testCase/TC5"}
  link(msg, iterationsMap[iteration]["TSS1"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC2"], "IUT")
  return msg

def generateTCS5(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS5", iteration)
  link(msg, iterationsMap[iteration]["TCT5"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF5(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF5", iteration)
  link(msg, iterationsMap[iteration]["TCT5"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.98), "conclusion": "SUCCESSFUL"}
  return msg

def generateTCT6(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT6", iteration)
  msg["data"]["testCase"] = {"tracker": "My Other Test Management System", "id": "TC6", "uri": "https://other-tm.company.com/testCase/TC6"}
  link(msg, iterationsMap[iteration]["TSS1"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC2"], "IUT")
  return msg

def generateTCS6(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS6", iteration)
  link(msg, iterationsMap[iteration]["TCT6"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF6(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF6", iteration)
  link(msg, iterationsMap[iteration]["TCT6"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.98), "conclusion": "SUCCESSFUL"}
  return msg

def generateTCT7(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseTriggeredEvent", t+timeToAdd, "1.0.0", "TCT7", iteration)
  msg["data"]["testCase"] = {"tracker": "My Other Test Management System", "id": "TC6", "uri": "https://other-tm.company.com/testCase/TC6"}
  link(msg, iterationsMap[iteration]["TSS1"], "CONTEXT")
  link(msg, iterationsMap[iteration]["ArtC2"], "IUT")
  return msg

def generateTCS7(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseStartedEvent", t+timeToAdd, "1.0.0", "TCS7", iteration)
  link(msg, iterationsMap[iteration]["TCT7"], "TEST_CASE_EXECUTION")
  return msg

def generateTCF7(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestCaseFinishedEvent", t+timeToAdd, "1.0.0", "TCF7", iteration)
  link(msg, iterationsMap[iteration]["TCT7"], "TEST_CASE_EXECUTION")
  msg["data"]["outcome"] = {"verdict": randomizeVerdict(0.98), "conclusion": "SUCCESSFUL"}
  return msg

def generateTSS1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestSuiteStartedEvent", t+timeToAdd, "1.0.0", "TSS1", iteration)
  link(msg, iterationsMap[iteration]["ActT3"], "CONTEXT")
  msg["data"]["name"] = "My functional test suite"
  msg["data"]["categories"] = ["Pre system integration tests"]
  msg["data"]["types"] = ["FUNCTIONAL"]
  return msg

def generateTSF1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelTestSuiteFinishedEvent", t+timeToAdd, "1.0.0", "TSF1", iteration)
  msg["data"]["outcome"] = {"verdict": getOutcomeValuesFromVerdicts([iterationsMap[iteration]["TCF5"], iterationsMap[iteration]["TCF6"], iterationsMap[iteration]["TCF7"]], "PASSED", "FAILED")}
  link(msg, iterationsMap[iteration]["TSS1"], "TEST_SUITE_EXECUTION")
  return msg

def generateCLM1(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelConfidenceLevelModifiedEvent", t+timeToAdd, "1.0.0", "CLM1", iteration)
  link(msg, iterationsMap[iteration]["ArtC1"], "SUBJECT")
  link(msg, iterationsMap[iteration]["TCF1"], "CAUSE")
  link(msg, iterationsMap[iteration]["TCF2"], "CAUSE")
  link(msg, iterationsMap[iteration]["TCF3"], "CAUSE")
  link(msg, iterationsMap[iteration]["TCF4"], "CAUSE")
  msg["data"]["name"] = "readyForRelease"
  msg["data"]["value"] = getOutcomeValuesFromVerdicts([iterationsMap[iteration]["TCF1"], iterationsMap[iteration]["TCF2"], iterationsMap[iteration]["TCF3"], iterationsMap[iteration]["TCF4"]], "SUCCESS", "FAILURE")
  return msg

def generateCLM2(iterationsMap, iteration, t, timeToAdd):
  msg = generateGenericMessage("EiffelConfidenceLevelModifiedEvent", t+timeToAdd, "1.0.0", "CLM2", iteration)
  msg["data"]["name"] = "readyForSystemIntegration"
  msg["data"]["value"] = getOutcomeValuesFromVerdicts([iterationsMap[iteration]["TSF1"]], "SUCCESS", "FAILURE")
  link(msg, iterationsMap[iteration]["TSF1"], "CAUSE")
  link(msg, iterationsMap[iteration]["ArtC2"], "SUBJECT")
  return msg

def buildMsgArrayFromiterationsMap(iterationsMap):
  globalArray = []
  for key, itMap in iterationsMap.items():
    if itMap:
      globalArray.extend(buildMsgArrayFromIterationMap(itMap))

  return globalArray

def buildMsgArrayFromIterationMap(iterationMap):
  msgArray = []
  for msg in iterationMap.values():
    msgArray.append(msg)

  return msgArray

def generateIterationZeroMessages(iterationsMap, t):
  iterationsMap[0] = {}
  iterationsMap[0]["SCS1"] = generateSCS1(iterationsMap, 0, t, 0)
  iterationsMap[0]["EDef1"] = generateEDef1(iterationsMap, 0, t, 1)
  iterationsMap[0]["EDef2"] = generateEDef2(iterationsMap, 0, t, 1)
  iterationsMap[0]["ArtC3"] = generateArtC3(iterationsMap, 0, t, 1)
  iterationsMap[0]["CDef3"] = generateCDef3(iterationsMap, 0, t, 1)
  iterationsMap[0]["ArtCC1"] = generateArtCC1(iterationsMap, 0, t, 1)
  iterationsMap[0]["ArtCC2"] = generateArtCC2(iterationsMap, 0, t, 1)
  iterationsMap[0]["ArtCC3"] = generateArtCC3(iterationsMap, 0, t, 1)

  return t

def generateComponentBuildEvents(iterationsMap, iteration, t):
  iterationsMap[iteration]["SCC1"] = generateSCC1(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["SCS1"] = generateSCS1(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["CDef3"] = generateCDef3(iterationsMap, iteration, t, 100)

  if random.random() < 0.5:
    iterationsMap[iteration]["ArtCC1"] = generateArtCC1(iterationsMap, iteration, t, 200000)

  if random.random() < 0.5:
    iterationsMap[iteration]["ArtCC2"] = generateArtCC2(iterationsMap, iteration, t, 35000)


  iterationsMap[iteration]["ArtCC3"] = generateArtCC3(iterationsMap, iteration, t, 1000)

  return t

def generateSubSystemBuildEvents(iterationsMap, iteration, t):
  iterationsMap[iteration]["ActT4"] = generateActT4(iterationsMap, iteration, t, 100)
  iterationsMap[iteration]["ActS4"] = generateActS4(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["CDef2"] = generateCDef2(iterationsMap, iteration, t, 100)

  if random.random() < 0.95:
    iterationsMap[iteration]["ArtC2"] = generateArtC2(iterationsMap, iteration, t, 100)
    iterationsMap[iteration]["ArtP2"] = generateArtP2(iterationsMap, iteration, t, 30000)


  iterationsMap[iteration]["ActF4"] = generateActF4(iterationsMap, iteration, t, 50)

  return t

def generateSubSystemTestEvents(iterationsMap, iteration, t):
  iterationsMap[iteration]["ActT3"] = generateActT3(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActS3"] = generateActS3(iterationsMap, iteration, t, 3)
  iterationsMap[iteration]["TSS1"] = generateTSS1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCT5"] = generateTCT5(iterationsMap, iteration, t, 100)
  iterationsMap[iteration]["TCT6"] = generateTCT6(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["TCT7"] = generateTCT7(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["TCS5"] = generateTCS5(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["TCS6"] = generateTCS6(iterationsMap, iteration, t, 2)
  iterationsMap[iteration]["TCS7"] = generateTCS7(iterationsMap, iteration, t, 1)
  iterationsMap[iteration]["TCF5"] = generateTCF5(iterationsMap, iteration, t, 10000)
  iterationsMap[iteration]["TCF6"] = generateTCF6(iterationsMap, iteration, t, 3000)
  iterationsMap[iteration]["TCF7"] = generateTCF7(iterationsMap, iteration, t, 5000)
  iterationsMap[iteration]["TSF1"] = generateTSF1(iterationsMap, iteration, t, 50)
  iterationsMap[iteration]["ActF3"] = generateActF3(iterationsMap, iteration, t, 3)
  iterationsMap[iteration]["CLM2"] = generateCLM2(iterationsMap, iteration, t, 300)
  
  return t

def generateSystemIntegrationEvents(iterationsMap, iteration, t):
  iterationsMap[iteration]["CDef1"] = generateCDef1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ArtC1"] = generateArtC1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ArtP1"] = generateArtP1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActT1"] = generateActT1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActS1"] = generateActS1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActT2"] = generateActT2(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCT1"] = generateTCT1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCT2"] = generateTCT2(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCS1"] = generateTCS1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCS2"] = generateTCS2(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCF2"] = generateTCF2(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCF1"] = generateTCF1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActF1"] = generateActF1(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActS2"] = generateActS2(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCT3"] = generateTCT3(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCS3"] = generateTCS3(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCF3"] = generateTCF3(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCT4"] = generateTCT4(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCS4"] = generateTCS4(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["TCF4"] = generateTCF4(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["ActF2"] = generateActF2(iterationsMap, iteration, t, 2000)
  iterationsMap[iteration]["CLM1"] = generateCLM1(iterationsMap, iteration, t, 2000)

  return t

def generateIterationMessages(iterationsMap, iteration, t):
  iterationsMap[iteration] = {}
  t = generateComponentBuildEvents(iterationsMap, iteration, t)
  t = generateSubSystemBuildEvents(iterationsMap, iteration, t)

  if "ArtC2" in iterationsMap[iteration]:
    t = generateSubSystemTestEvents(iterationsMap, iteration, t)
    if iterationsMap[iteration]["CLM2"]["data"]["value"] == "SUCCESS":
      t = generateSystemIntegrationEvents(iterationsMap, iteration, t)

  return t

def main(iterations):
  t = int(time.time() * 1000)

  iterationsMap = {}

  t = generateIterationZeroMessages(iterationsMap, t)

  for iteration in range(1, iterations + 1):
    t += 10000
    t = generateIterationMessages(iterationsMap, iteration, t)

  out = buildMsgArrayFromiterationsMap(iterationsMap)

  out.sort(key=lambda x: x["meta"]["time"], reverse=False)
  print(json.dumps(out, indent=2, separators=(",", ": ")))

def usage():
  print("-h, --help")
  print("    Print this text.")
  print("-i ..., --iterations=...")
  print("    Specify the number of iterations to create.")
  print("    Default: 1")

try:
  opts, args = getopt.getopt(sys.argv[1:], "hi:", ["help", "iterations="])
except getopt.GetoptError:
  usage()
  sys.exit(2)

iterations = 1

for opt, arg in opts:
  if opt in ("-h", "--help"):
    usage()
    sys.exit()
  elif opt in ("-i", "--iterations"):
    iterations = int(arg)

main(iterations)
