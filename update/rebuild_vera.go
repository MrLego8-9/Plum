package update

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
)

const veraUrl = "https://github.com/Epitech/banana-vera.git"
const veraFolder = "/tmp/banana-vera"
const veraCMakeLists = veraFolder + "/src/CMakeLists.txt"
const veraCMakeGenerateArgs = "-B build . -DVERA_LUA=OFF -DPANDOC=OFF -DVERA_USE_SYSTEM_BOOST=ON"
const veraCMakeBuildArgs = "--build build -j"

var veraCmakeFlags = []string{"target_compile_options(vera PRIVATE", "  -Ofast", "  -march=native", ")",
	"target_link_options(vera PRIVATE", "  -flto=auto", ")"}

func cloneVera() { // Clone vera repo in /tmp
	removeVeraErr := os.RemoveAll(veraFolder)
	if removeVeraErr != nil {
		log.Fatal("Remove vera tmp directory ", removeVeraErr)
	}
	cloneVeraErr := exec.Command("git", "clone", veraUrl, veraFolder).Run()
	if cloneVeraErr != nil {
		log.Fatal("Clone vera ", cloneVeraErr)
	}
}

func execCommandInVeraFolder(cmd string, args ...string) error {
	command := exec.Command(cmd, args...)
	command.Dir = veraFolder
	command.Stderr = os.Stderr
	command.Stdout = os.Stdout
	return command.Run()
}

func runCommandAsRoot(cmd string, args ...string) *exec.Cmd {
	if os.Getuid() != 0 {
		return exec.Command("/bin/sudo", append([]string{cmd}, args...)...)
	} else {
		return exec.Command(cmd, args...)
	}
}

func addBuildFlags() { // Adds the build flags to the vera Cmake
	cmakeListsHandleRd, openErr := os.OpenFile(veraCMakeLists, os.O_RDONLY, 0644)
	if openErr != nil {
		log.Fatal("open Cmake in read-only mode ", openErr)
	}
	cmakeStat, statErr := cmakeListsHandleRd.Stat()
	if statErr != nil {
		log.Fatal("Cmake stat ", statErr)
	}
	fileBuffer := make([]byte, cmakeStat.Size())
	bytesRead, readErr := cmakeListsHandleRd.Read(fileBuffer)
	if readErr != nil {
		log.Fatal("Read Cmake ", readErr)
	}
	cmakeString := string(fileBuffer[:bytesRead])
	closeRdErr := cmakeListsHandleRd.Close()
	if closeRdErr != nil {
		log.Fatal("Close Cmake in read-only mode ", closeRdErr)
	}
	cmakeLines := strings.Split(cmakeString, "\n")
	for idx, line := range cmakeLines { // Find line to add the flags to
		if line == "add_executable(vera ${srcs})" {
			fileEnd := make([]string, len(cmakeLines[idx+1:]))
			copy(fileEnd, cmakeLines[idx+1:])
			modifiedPartialCmake := append(cmakeLines[:idx+1], veraCmakeFlags...)
			cmakeLines = append(modifiedPartialCmake, fileEnd...)
			break
		}
	}
	cmakeString = strings.Join(cmakeLines, "\n")
	// Close and reopen the file to clear it, to avoid duplication
	cmakeListsHandleWr, openWrErr := os.OpenFile(veraCMakeLists, os.O_WRONLY|os.O_TRUNC, 0644)
	if openWrErr != nil {
		log.Fatal("open Cmake write mode ", openWrErr)
	}
	bytesWritten, writeErr := cmakeListsHandleWr.Write([]byte(cmakeString))
	if writeErr != nil {
		log.Fatal("Write Cmake ", writeErr)
	}
	if bytesWritten != len(cmakeString) {
		log.Fatal("Failed to properly overwrite CMake")
	}
	closeErr := cmakeListsHandleWr.Close()
	if closeErr != nil {
		log.Fatal("Close Cmake write mode ", closeErr)
	}
}

func buildVera() {
	generateErr := execCommandInVeraFolder("cmake", strings.Split(veraCMakeGenerateArgs, " ")...)
	if generateErr != nil {
		log.Fatal("Generate CMake ", generateErr)
	}
	buildErr := execCommandInVeraFolder("cmake", strings.Split(veraCMakeBuildArgs, " ")...)
	if buildErr != nil {
		log.Fatal("Build Vera ", buildErr)
	}
}

func RebuildVera() {
	cloneVera()
	addBuildFlags()
	buildVera()
	// Needs root access to copy vera in the correct folder
	copyCommand := runCommandAsRoot("cp", veraFolder+"/build/src/vera++", "/usr/local/bin/")
	copyCommand.Stdout = os.Stdout
	copyCommand.Stderr = os.Stderr
	copyCommand.Stdin = os.Stdin
	copyErr := copyCommand.Run()
	if copyErr != nil {
		log.Fatal("Copy Vera ", copyErr)
	}
	removeVeraErr := os.RemoveAll(veraFolder)
	if removeVeraErr != nil {
		log.Fatal("Remove vera tmp directory post-build ", removeVeraErr)
	}
	fmt.Println("\n -> Vera rebuilt successfully")
}
