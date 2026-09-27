document.getElementById("summarize-form").addEventListener("submit", async function (event) {
  event.preventDefault();

  var text = document.getElementById("text-input").value;
  var method = document.getElementById("method-select").value;
  var numSentences = parseInt(document.getElementById("sentences-input").value, 10);

  var statusEl = document.getElementById("status");
  var resultEl = document.getElementById("result");
  var submitBtn = document.getElementById("submit-btn");

  resultEl.hidden = true;
  statusEl.hidden = false;
  statusEl.className = "status loading";
  statusEl.textContent = "Summarizing...";
  submitBtn.disabled = true;

  try {
    var response = await fetch("/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: text,
        method: method,
        num_sentences: numSentences
      })
    });

    var data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Something went wrong.");
    }

    statusEl.hidden = true;
    resultEl.hidden = false;
    document.getElementById("summary-text").textContent = data.summary;
    document.getElementById("word-stats").textContent =
      data.original_words + " words -> " + data.summary_words + " words (" +
      data.method + ", " + data.num_sentences + " sentences)";
  } catch (err) {
    statusEl.className = "status error";
    statusEl.textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});
