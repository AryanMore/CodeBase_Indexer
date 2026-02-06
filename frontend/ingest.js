const ingestBtn = document.getElementById("ingest-btn");
const useExistingBtn = document.getElementById("use-existing-btn");
const repoInput = document.getElementById("repo-url");
const ingestStatus = document.getElementById("ingest-status");
const ingestSpinner = document.getElementById("ingest-spinner");

ingestBtn.addEventListener("click", async () => {
    const repoUrl = repoInput.value.trim();
    if (!repoUrl) {
        ingestStatus.textContent = "Please enter a repository URL.";
        return;
    }

    ingestStatus.textContent = "Ingesting repository…";
    ingestSpinner.classList.remove("hidden");
    ingestBtn.disabled = true;
    useExistingBtn.disabled = true;

    try {
        const response = await fetch("/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        if (!response.ok) throw new Error();
        window.location.href = "/chat";

    } catch {
        ingestStatus.textContent = "Error during ingestion.";
        ingestBtn.disabled = false;
        useExistingBtn.disabled = false;
        ingestSpinner.classList.add("hidden");
    }
});

useExistingBtn.addEventListener("click", async () => {
    ingestStatus.textContent = "";
    ingestSpinner.classList.remove("hidden");
    ingestBtn.disabled = true;
    useExistingBtn.disabled = true;

    try {
        const response = await fetch("/has_index");
        if (!response.ok) throw new Error();

        const data = await response.json();
        if (!data.has_index) {
            ingestStatus.textContent = "No existing index found.";
            ingestBtn.disabled = false;
            useExistingBtn.disabled = false;
            ingestSpinner.classList.add("hidden");
            return;
        }

        window.location.href = "/chat";

    } catch {
        ingestStatus.textContent = "Error checking existing index.";
        ingestBtn.disabled = false;
        useExistingBtn.disabled = false;
        ingestSpinner.classList.add("hidden");
    }
});
