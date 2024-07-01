package io

import (
	"os"
	"os/exec"
	"sort"
	"strings"
)

func ConvertToStringArray(input []byte) []string {
	strInput := strings.Trim(string(input), "\n")
	return strings.Split(strInput, "\n")
}

func getUniqueGitDirs(gitDirsBytes []byte) []string {
	gitDirs := ConvertToStringArray(gitDirsBytes)
	sort.Slice(gitDirs, func(i, j int) bool {
		return len(gitDirs[i]) < len(gitDirs[j])
	})

	uniqueDirectories := make([]string, 0)
gitUniqueDirs:
	for _, dir := range gitDirs {
		dir = strings.TrimPrefix(dir, "./")
		for _, uniqueDir := range uniqueDirectories {
			if strings.HasPrefix(dir, uniqueDir) {
				continue gitUniqueDirs
			}
		}
		uniqueDirectories = append(uniqueDirectories, dir)
	}
	return uniqueDirectories
}

func getUniqueGitFiles(gitFilesBytes []byte, uniqueDirs []string) []string {
	gitFiles := ConvertToStringArray(gitFilesBytes)
	sort.Slice(gitFiles, func(i, j int) bool {
		return len(gitFiles[i]) < len(gitFiles[j])
	})
	uniqueFiles := make([]string, 0)
gitUniqueFiles:
	for _, file := range gitFiles {
		file = strings.TrimPrefix(file, "./")
		for _, uniqueDir := range uniqueDirs {
			if strings.HasPrefix(file, uniqueDir) {
				continue gitUniqueFiles
			}
		}
		uniqueFiles = append(uniqueFiles, file)
	}
	return uniqueFiles
}

func readPlumIgnore() ([]byte, error) {
	plumIgnoreHandle, err := os.Open(".plumignore")
	if err != nil {
		return nil, err
	}
	fileStat, statErr := plumIgnoreHandle.Stat()
	if statErr != nil {
		return nil, statErr
	}
	fileBuffer := make([]byte, fileStat.Size())
	bytesRead, readErr := plumIgnoreHandle.Read(fileBuffer)
	if readErr != nil {
		return nil, readErr
	}
	closeErr := plumIgnoreHandle.Close()
	if closeErr != nil {
		return nil, closeErr
	}
	return fileBuffer[:bytesRead], nil
}

func isPathUnique(path string, uniqueDirs []string) bool {
	for _, uniqueDir := range uniqueDirs {
		if strings.HasPrefix(path, uniqueDir) {
			return false
		}
	}
	return true
}

func getPlumFiles(plumIgnoreBytes []byte, uniqueDirs []string, uniqueFiles []string) ([]string, []string) {
	plumIgnoreContent := ConvertToStringArray(plumIgnoreBytes)
	for _, line := range plumIgnoreContent {
		if strings.HasPrefix(line, "./") {
			line = strings.TrimPrefix(line, "./")
		}
		line = strings.TrimRight(line, "/")
		if strings.Contains(line, "*") { // Allow wildcards ignores in .plumignore
			uniqueFiles = append(uniqueFiles, line)
			continue
		}
		fileStat, statErr := os.Lstat(line)
		if !os.IsNotExist(statErr) && isPathUnique(line, uniqueDirs) {
			if fileStat.IsDir() {
				uniqueDirs = append(uniqueDirs, line)
			} else {
				uniqueFiles = append(uniqueFiles, line)
			}
		}
	}
	return uniqueDirs, uniqueFiles
}

func GetIgnoredFiles(ignoreProcessing bool) ([]string, []string, error) {
	if ignoreProcessing {
		return []string{}, []string{}, nil
	}
	getGitDirs := exec.Command("bash", "-c", "git check-ignore $(find . -type d -print)")
	getGitFiles := exec.Command("bash", "-c", "git check-ignore $(find . -type f -print)")
	gitDirsBytes, gitDirsErr := getGitDirs.Output()
	uniqueDirectories := make([]string, 0)
	if gitDirsErr == nil {
		uniqueDirectories = getUniqueGitDirs(gitDirsBytes)
	}
	gitFilesBytes, gitFilesErr := getGitFiles.Output()
	uniqueFiles := make([]string, 0)
	if gitFilesErr == nil {
		uniqueFiles = getUniqueGitFiles(gitFilesBytes, uniqueDirectories)
	}

	plumIgnoreBytes, plumIgnoreErr := readPlumIgnore()
	if plumIgnoreErr == nil {
		uniqueDirectories, uniqueFiles = getPlumFiles(plumIgnoreBytes, uniqueDirectories, uniqueFiles)
	}
	return uniqueDirectories, uniqueFiles, nil
}
