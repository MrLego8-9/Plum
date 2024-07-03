package update

import (
	"log"
	"os"
	"os/exec"
)

const updateDirectory = "/tmp/Plum"
const plumBinaryPos = "/bin/plum"

const dockerVolumeDirectory = "/tmp/docker-volume"
const dockerScript = "#!/bin/bash\ncp /usr/local/bin/lambdananas /mounted-dir\ncp -r /usr/local/lib/vera++ /mounted-dir"
const dockerEntrypoint = "--entrypoint=/mounted-dir/copy.sh"
const dockerImage = "ghcr.io/epitech/coding-style-checker:latest"
const dockerContainerName = "code-style-tmp"

func handleDockerInteraction() {
	removeDockerErr := os.RemoveAll(dockerVolumeDirectory)
	if removeDockerErr != nil {
		log.Fatal("Remove temp docker volume", removeDockerErr)
	}
	mkDockerErr := os.MkdirAll(dockerVolumeDirectory, 0755)
	if mkDockerErr != nil {
		log.Fatal("Mkdir docker volume", mkDockerErr)
	}
	createDockerScriptErr := os.WriteFile("/tmp/docker-volume/copy.sh", []byte(dockerScript), 0755)
	if createDockerScriptErr != nil {
		log.Fatal("Create docker script", createDockerScriptErr)
	}
	pullDockerErr := exec.Command("docker", "pull", dockerImage).Run()
	if pullDockerErr != nil {
		log.Fatal("Pull docker image", pullDockerErr)
	}
	dockerRunCmd := exec.Command("docker", "run", "--name", dockerContainerName, "-v", dockerVolumeDirectory+":/mounted-dir", dockerEntrypoint, dockerImage)
	dockerRunCmd.Stderr = os.Stderr
	dockerRunCmd.Stdout = os.Stdout
	dockerRunErr := dockerRunCmd.Run()
	if dockerRunErr != nil {
		log.Fatal("Run docker container", dockerRunErr)
	}
	removeContainerErr := exec.Command("docker", "rm", dockerContainerName).Run()
	if removeContainerErr != nil {
		log.Fatal("Remove docker container", removeContainerErr)
	}
}

func moveDockerContents() {
	moveVeraDirErr := exec.Command("cp", "-r", dockerVolumeDirectory+"/vera++", "/usr/local/lib/vera++").Run()
	if moveVeraDirErr != nil {
		log.Fatal("Move vera directory", moveVeraDirErr)
	}
	moveLambdananas := exec.Command("cp", dockerVolumeDirectory+"/lambdananas", "/bin/lambdananas").Run()
	if moveLambdananas != nil {
		log.Fatal("Move lambdananas", moveLambdananas)
	}
}

func buildPlumBinary() {
	buildPlum := exec.Command("go", "build", "-tags", "netgo")
	buildPlum.Dir = updateDirectory
	buildPlum.Stdout = os.Stdout
	buildPlum.Stderr = os.Stderr
	buildPlum.Stdin = os.Stdin
	buildErr := buildPlum.Run()
	if buildErr != nil {
		log.Fatal("Build plum", buildErr)
	}
	movePlumErr := exec.Command("cp", updateDirectory+"/plum", plumBinaryPos).Run()
	if movePlumErr != nil {
		log.Fatal("Move plum", movePlumErr)
	}
}

func PlumUpdateRules() {
	removeRepoErr := os.RemoveAll(updateDirectory)
	if removeRepoErr != nil {
		log.Println("Remove temp repository", removeRepoErr)
	}
	gitCloneErr := exec.Command("git", "clone", "https://github.com/MrLego8-9/Plum.git", updateDirectory).Run()
	if gitCloneErr != nil {
		log.Fatal("Clone temp repository", gitCloneErr)
	}
	handleDockerInteraction()
	moveDockerContents()
	if _, goNotFound := exec.LookPath("go"); goNotFound != nil {
		removePlumErr := os.Remove(plumBinaryPos)
		if removePlumErr != nil {
			log.Fatal("Remove plum", removePlumErr)
		}
		downloadErr := downloadPlumBinary(plumBinaryPos)
		if downloadErr != nil {
			log.Fatal("Download plum", downloadErr)
		}
	} else {
		buildPlumBinary()
	}
	removeDockerVolumeErr := os.RemoveAll(dockerVolumeDirectory)
	if removeDockerVolumeErr != nil {
		log.Fatal("Remove docker volume", removeDockerVolumeErr)
	}
}
