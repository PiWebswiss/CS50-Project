// Define elements
const uploadFile = document.getElementById("uploadFile");
const dropArea = document.getElementById("dropArea");
const fileInput = document.getElementById("fileInput");
const userFeedBack = document.getElementById("userFeedBack");
const animatedText = document.getElementById("animatedText");
const btnCopy = document.getElementById("btnCopy");
const tBody = document.getElementById("tBody");
const deleteBtn = document.getElementById("deleteBtn");
const deleteResponse = document.getElementById("deleteResponse");

// Initialize variable to save the current predicted text
let saveText;

// Text animation code modified from GPT4
function typeText(text, element, maxLength = 290) {
    // Clear existing text 
    element.textContent = "";
    let index = 0;

    // Create the cursor element 
    const cursorSpan = document.createElement("span");
    cursorSpan.classList.add("cursor");
    cursorSpan.textContent = "|";
    element.appendChild(cursorSpan);

    // Function to animate text typing
    function type() {
        if (index < text.length && index < maxLength) {
            // Update the text content with the next character
            element.textContent = text.substring(0, index + 1);
            // Re-append the cursor to ensure it stays at end
            element.appendChild(cursorSpan);
            index++;
            setTimeout(type, 100); // Adjust typing speed as needed
        } else {
            if (index >= maxLength) {
                element.textContent = text.substring(0, maxLength) + "...";
            }
            // Remove the cursor after typing
            cursorSpan.remove();
        }
    }
    type();
}

// Function to hide the user feedback message
function hideFeedback(time) {
    setTimeout(() => {
        userFeedBack.style.display = "none";
        userFeedBack.classList.remove("success", "error", "info");
    }, time);
}

// Function to adjust width of feedback box
function adjustWidth(element) {
    const computeWidth = element.scrollWidth;
    element.style.width = computeWidth + "px";
}

// Display user feedback
function showFeedback(message, type) {
    userFeedBack.innerText = message;
    userFeedBack.classList.add(type);
    userFeedBack.style.display = "block";
    adjustWidth(userFeedBack);
    hideFeedback(5000); // hide after 5 seconds
}

// Function to handle drag-and-drop events
function handleDrag(event) {
    // Prevent default behavior and stop event propagation
    event.preventDefault();
    event.stopPropagation();

    // Visual feedback for drag-and-drop
    switch (event.type) {
        case "dragenter":
        case "dragover":
            dropArea.classList.add("dragover");
            break;
        case "dragleave":
        case "drop":
            dropArea.classList.remove("dragover");
            break;
    }

    // Handle file drop event
    if (event.type === "drop") {
        // Retrieve files from the event
        const files = event.dataTransfer.files;
        handleFileUpload(files);
    }
}

// Function to setup the application
function setupApplication() {
    // Add drag-and-drop functionality
    if (dropArea) {
        ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
            dropArea.addEventListener(eventName, handleDrag, false);
        });

        // Handling file selection
        fileInput.addEventListener("change", (event) => {
            handleFileUpload(event.target.files);
        });
    }
}

setupApplication();

// Setup all copy buttons in the table
function setupTableCopyBtn() {
    // Select all buttons
    let tableBtnCopy = document.querySelectorAll(".table-copy-btn");

    tableBtnCopy.forEach(button => {
        // Add click event to each button
        button.addEventListener("click", () => {

            // Get the ID of the text element to copy from the data-clipboard-id attribute
            let textElementID = button.getAttribute("data-clipboard-id");

            // Get the text content of the element
            let textToCopy = document.getElementById(textElementID).textContent;

            // Copy the text to the clipboard
            copyTextClipboard(textToCopy);
        });
    });
}

// Function to send and receive response
async function fetchDataViaPost(route) {
    if (!route) {
        return null;
    }
    try {
        let response = await fetch(route, {
            method: "POST",
        });

        // Check response and get the results
        if (response.ok) {
            let results = await response.json();
            return results;
        }

    } catch (error) {
        console.error("Error fetching data:", error);
        return null;
    }
}

// Function to add rows to the table
async function showResultsTable() {
    // Get the data
    let data = await fetchDataViaPost(path = "/results");

    // Clear existing rows
    tBody.innerHTML = "";

    // Ensure we have data
    if (data) {
        // Iterate over the results and add rows to table
        data.forEach((item, index) => {
            let row = document.createElement("tr");
            row.setAttribute("scope", "row");

            // Insert the date and time 
            let datetimeCell = document.createElement("td");
            datetimeCell.classList.add("hide-on-small");
            datetimeCell.textContent = item.datetime;
            row.appendChild(datetimeCell);

            // Insert the text
            let textCell = document.createElement("td");
            textCell.id = `text-${index + 1}`;
            textCell.classList.add("truncate-text");
            textCell.textContent = item.text;
            row.appendChild(textCell);

            // Setup button to copy text
            let buttonCell = document.createElement("td");
            let button = document.createElement("button");
            button.id = `copy-btn-${index + 1}`;
            button.setAttribute("data-clipboard-id", `text-${index + 1}`);
            button.classList.add("table-copy-btn");
            button.textContent = "Copy text";
            buttonCell.appendChild(button);
            row.appendChild(buttonCell);

            tBody.appendChild(row);
        });
        // Setup copy text button
        setupTableCopyBtn();
    }
}

// Call function
showResultsTable();

// Function to handle file upload
async function handleFileUpload(files) {
    // Ensure files are valid
    if (files.length === 0) {
        showFeedback("Please provide at least one file.", "error");
        return;
    }
    // Select a single OCR Model
    let ocrModel = document.querySelector('input[name="ocr_model"]:checked');

    // Ensure OCR Model is valid
    if (!ocrModel) {
        showFeedback("Please choose at least one OCR model.", "error");
        return;
    }

    // Construct a set of key/value pairs
    let formData = new FormData();
    formData.append('file', files[0]);
    // Append the OCR model 
    formData.append("ocrModel", ocrModel.value);

    // Show info message processing
    showFeedback("Processing your request...", "info");

    // Using AJAX for submitting the form (code modified from GPT4)
    try {
        let response = await fetch("/submit", {
            method: "POST",
            body: formData,
        });

        let result = await response.json();

        // Ensure response is valid
        if (!response.ok) {
            showFeedback(result.error, "error");
            return;
        }

        // Access data
        if ("ocr_result" in result) {
            typeText(result.ocr_result, animatedText);
            saveText = result.ocr_result;
            showResultsTable();
            showFeedback("Successfully performed OCR.", "success");

            // Clear file input after OCR is done
            fileInput.value = "";

        } else if ("error" in result) {
            showFeedback(result.error, "error");
        } else {
            showFeedback("Invalid request.", "error");

        }
    } catch (error) {
        console.error("Error during file upload:", error);
        showFeedback("Invalid request.", "error");
    }
}

// Handle form submission via AJAX 
uploadFile.addEventListener("submit", async (event) => {
    // Prevent the form from submitting
    event.preventDefault();

    let files;
    try {
        files = fileInput.files;
    } catch (error) {
        console.error("Error accessing files:", error);
        showFeedback("Please provide at least one file.", "error");
        return;
    }
    handleFileUpload(files);
});

// Function to copy text inside the Clipboard 
function copyTextClipboard(text) {
    // Replace "\n" by a space
    text = text.replace("\n", " ");

    navigator.clipboard.writeText(text)
        .then(() => {
            showFeedback("Text copied", "info");
        })
        .catch(err => {
            console.error("Error copying text:", err);
            showFeedback("Failed to copy text", "error");
        });
}

// Button to copy text 
btnCopy.addEventListener("click", () => {
    if (!saveText) {
        showFeedback("No text to copy", "info");
        return;
    }

    // Copy text inside the Clipboard
    copyTextClipboard(saveText);
});

// Function to show a message for a specified duration
function showMessageFor(element, message, time=5000) {
    // Display the message
    element.innerText = message;
    setTimeout(() => {
        // Clear the message
        element.innerText = "";
    }, time);
}

// Setup button to remove cookie and user data from database
deleteBtn.addEventListener("click", async () => {
    // Clear any previous response 
    deleteResponse.innerText = "";

    // Send to the server to delete user
    let result = await fetchDataViaPost(path = "/delete");
    try {
        // Message Handling: Determine which message to display
        if ("message" in result) {
            // Show message
            showMessageFor(deleteResponse, result.message);
            // Upadate the table
            showResultsTable();

        } else if ("info" in result) {
            // Show info
            showMessageFor(deleteResponse, result.info);
        } else {
            // Show error
            showMessageFor(deleteResponse, result.error);
        }
    }
    // Show error message
    catch (error) {
        console.error("Error deleting data:", error);
        // Message: Could not delete your data
        showMessageFor(deleteResponse, "Could not delete your data.");

    }
});

// Footer
// Create a new Date object
const date = new Date();
// Get the footerDate element by its id
const footerDate = document.getElementById("footerDate");
// Populate the footerDate element with the current year
footerDate.innerHTML = `Project CS50x &copy; Harvard University - ${date.getFullYear()}`;