package io

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

type CheckResult struct {
	ErrorCount map[string]int
	Errors     [][]string
}

const (
	FATAL_COLOR   = "\033[91;1;4m"
	MAJOR_COLOR   = "\033[91;1m"
	MINOR_COLOR   = "\033[93;1m"
	INFO_COLOR    = "\033[96;1m"
	TITLE_COLOR   = "\033[1m"
	SPECIAL_COLOR = "\033[94;1m"
	FILE_COLOR    = "\033[90m"
	OK_COLOR      = "\033[92m"
	NO_COLOR      = "\033[0m"
)

const filenameIndex = 0
const ( // Error tokens constants
	lineIndex int = iota
	severityIndex
	errorCodeIndex
	errorMeaningIndex
)

var errorsKeys = []string{"INFO", "MINOR", "MAJOR", "FATAL"}
var errorColorsMap = map[string]string{"FATAL": FATAL_COLOR, "MAJOR": MAJOR_COLOR, "MINOR": MINOR_COLOR, "INFO": INFO_COLOR}

func printErrorReport(errorCount map[string]int) {
	fmt.Printf("%s[FATAL]%s : %d | ", FATAL_COLOR, NO_COLOR, errorCount["FATAL"])
	fmt.Printf("%s[MAJOR]%s : %d | ", MAJOR_COLOR, NO_COLOR, errorCount["MAJOR"])
	fmt.Printf("%s[MINOR]%s : %d | ", MINOR_COLOR, NO_COLOR, errorCount["MINOR"])
	fmt.Printf("%s[INFO]%s : %d\n", INFO_COLOR, NO_COLOR, errorCount["INFO"])
}

func getFileErrorsMap(errors [][]string) map[string][][]string {
	fileErrorsMap := make(map[string][][]string)
	for _, styleError := range errors {
		filename := styleError[filenameIndex]
		if _, ok := fileErrorsMap[filename]; ok {
			fileErrorsMap[filename] = append(fileErrorsMap[filename], styleError[1:])
		} else {
			fileErrorsMap[filename] = make([][]string, 0)
			fileErrorsMap[filename] = append(fileErrorsMap[filename], styleError[1:])
		}
	}
	return fileErrorsMap
}

func printError(filename string, errorTokens []string) {
	fmt.Print("    ")
	nbTokens := len(errorTokens)
	if nbTokens == 1 {
		fmt.Printf("%s[SPECIAL]%s - %s %s(%s)%s\n", SPECIAL_COLOR, NO_COLOR, errorTokens[0], FILE_COLOR, filename, NO_COLOR)
		return
	}
	errorTokens[nbTokens-1] = strings.Trim(errorTokens[nbTokens-1], "\n")
	if errorColor, ok := errorColorsMap[errorTokens[severityIndex]]; ok {
		fmt.Printf("%s[%s] (%s)%s - %s %s(%s:%s)%s\n", errorColor, errorTokens[severityIndex],
			errorTokens[errorCodeIndex], NO_COLOR, errorTokens[errorMeaningIndex], FILE_COLOR, filename,
			errorTokens[lineIndex], NO_COLOR)
	} else {
		errorContent := strings.Join(errorTokens[1:], "")
		fmt.Printf("%s[SPECIAL]%s - %s %s(%s:%s)%s\n", SPECIAL_COLOR, NO_COLOR, errorContent, FILE_COLOR,
			filename, errorTokens[lineIndex], NO_COLOR)
	}
}

func printErrorsMap(errorsMap map[string][][]string) {
	for filename, styleErrors := range errorsMap {
		sort.Slice(styleErrors, func(i, j int) bool {
			val1, v1err := strconv.Atoi(styleErrors[i][0])
			if v1err != nil {
				panic(v1err)
			}
			val2, v2err := strconv.Atoi(styleErrors[j][0])
			if v2err != nil {
				panic(v2err)
			}
			return val1 < val2
		})
		fmt.Printf("\n%s‣ In File %s%s\n", TITLE_COLOR, filename, NO_COLOR)
		for _, styleError := range styleErrors {
			printError(filename, styleError)
		}
	}
}

func PrintErrors(cErrors, haskellErrors CheckResult) bool {
	cErrorsSum := 0
	haskellErrorsSum := 0
	globalErrors := make(map[string]int)
	for _, key := range errorsKeys {
		cErrorsSum += cErrors.ErrorCount[key]
		haskellErrorsSum += haskellErrors.ErrorCount[key]
		globalErrors[key] = cErrors.ErrorCount[key] + haskellErrors.ErrorCount[key]
	}
	totalErrorsSum := cErrorsSum + haskellErrorsSum

	if totalErrorsSum == 0 { // Exit early if no errors
		fmt.Printf("%sNo errors found%s\n", OK_COLOR, NO_COLOR)
		return false
	}

	if cErrorsSum > 0 {
		cErrorsMap := getFileErrorsMap(cErrors.Errors)
		fmt.Printf("\n%sC Style results%s\n\n", INFO_COLOR, NO_COLOR)
		printErrorsMap(cErrorsMap)
	}
	if haskellErrorsSum > 0 {
		haskellErrorsMap := getFileErrorsMap(haskellErrors.Errors)
		fmt.Printf("\n%sHaskell Style results%s\n\n", INFO_COLOR, NO_COLOR)
		printErrorsMap(haskellErrorsMap)
	}

	// Print error reports
	if cErrorsSum > 0 {
		fmt.Printf("\n%sC Error Report:%s\n", TITLE_COLOR, NO_COLOR)
		printErrorReport(cErrors.ErrorCount)
	}
	if haskellErrorsSum > 0 {
		fmt.Printf("\n%sHaskell Error Report:%s\n", TITLE_COLOR, NO_COLOR)
		printErrorReport(haskellErrors.ErrorCount)
	}
	fmt.Printf("\n%sGlobal Error Report:%s\n", TITLE_COLOR, NO_COLOR)
	printErrorReport(globalErrors)
	return true
}
