/* Nav bar */
/* const navbarID = document.getElementById("navbar")

// Fonction to handle nav bar scroll event
function navScroll(scroll) {
    if (window.scrollY > scroll) {
        navbarID.classList.add("scrolled")
    }
    else {
        navbarID.classList.remove("scrolled")
    }
}

window.addEventListener("scroll", () => {
    navScroll(200);
});
 */


const uploadFile = document.getElementById("uploadFile");
const fileInput = document.getElementById("fileInput");
const dropArea = document.getElementById('drop-area');
const userFeedBack = document.getElementById("userFeedBack");
const animatedText = document.getElementById("animatedText");
const btnCopy = document.getElementById("btnCopy");
const tableBtnCopy = document.querySelectorAll(".table-copy-btn");




// Initialize variable to save the current predicted text
let saveText;

/* Text animation code modified from GPT4 */
function typeText(text, element, maxLength=300) {
    // Clear existing text 
    element.textContent = "";
    let index = 0;

    // Create the cursor element 
    const cursorSpan = document.createElement("span");
    cursorSpan.classList.add("cursor");
    cursorSpan.textContent = "|";
    element.appendChild(cursorSpan);

    function type() {
        if (index < text.length && index < maxLength) {
            // Update the text content with the next character
            element.textContent = text.substring(0, index + 1);
            // Re-append the cursor to ensure it stays at end
            element.appendChild(cursorSpan);
            index++;
            setTimeout(type, 100); // Adjust typing seed as needed
        }
        else {
            if (index >= maxLength) {
                element.textContent =  text.substring(0, maxLength) + "...";
            }   
            // Remove the cursor after typing
            cursorSpan.remove();   
        }  
    }
    type();
}

// Function to hide the user feedback message
function hidFeedback(time) {
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
    hidFeedback(5000); // hide after 5 seconds
}

// Function to handle drag-and-drop events
function handleDrag(event) {
    // Prevent default behavior and stop event propagation
    event.preventDefault();
    event.stopPropagation();

    // Visual feedback for drag-and-drop
    switch(event.type) {
        case 'dragenter':
        case 'dragover':
            dropArea.classList.add('dragover');
            break;
        case 'dragleave':
        case 'drop':
            dropArea.classList.remove('dragover');
            break;
    }

    // Handle file drop event
    if (event.type === 'drop') {
        // Retrive files from the event
        const files = event.dataTransfer.files
        handleFileUpload(files);
    }
}

// Function to setup the application
function setupApplication() {
    // Add drag-and-drop functionality
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, handleDrag, false);
        });

        // Add click event to Open file selector
        dropArea.addEventListener("click", () => {
            // open the file selector
            fileInput.click();
        });

        // Handeling file selection
        fileInput.addEventListener("change", (event) => {
            handleFileUpload(event.target.files);
        });
    }
}
setupApplication()

// Function to handle file upload
/* Using AJAX for submiting the form (code modified from GPT4) */
async function handleFileUpload(files) {
     // Ensure files is valide
    if (files.length === 0) {
        showFeedback("Please provide at least one file.", "error");
        return;
    }
    // Select a single OCR Model
    const ocrModel = document.querySelector('input[name="ocr_model"]:checked');

    // Ensure OCR Model is valide
    if (!ocrModel) {
        showFeedback("Please chose at least one OCR model.", "error");
        return;
    }

    // Construct a set of key/values dict
    const formData = new FormData(uploadFile);
    
    // Append the values
    formData.append("file", files[0]);
    formData.append("ocrModel", ocrModel.value)

    // Show info message processing
    showFeedback("Processing your request...", "info");

    try {
        let responce = await fetch("/submit", {
            method: "POST",
            body: formData,
        });
            
        let result = await responce.json();

        console.log(result) /* I got the message */

        // Ensure responce is valid
        if (!responce.ok) {
            showFeedback(result.error, "error");
            return;
        }
        
        // Access data
        if ("ocr_result" in result) {
            typeText(result.ocr_result, animatedText);
            saveText = result.ocr_result;
            showFeedback("Successfully perform OCR.", "success");

        // Clear file input after OCR is done
        fileInput.value = "";
           
        }
        else if ("erro" in result) {
            showFeedback(result.error, "error");
        }
        else{
            showFeedback("Invalid request.", "error");
            
        }
    } catch (error) {
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
    } catch (erro) {
        showFeedback("Please provide at least one file.", "error")
        return;
    }
    handleFileUpload(files)
});

/* Function to copy text inside the Clipboard  */
function copyTextClipboard(text) {
    // Replace '\n' by a space
    text = text.replace("\n", " ");

    navigator.clipboard.writeText(text)
    .then(() => {
        showFeedback("Text copied", "info");
    })
    .catch(err => {
        showFeedback("Failed to copy text", "error");
    });
}

/* Button to copy text  */
btnCopy.addEventListener("click", () => {
    if (!saveText) {
        showFeedback("No text to copy", "info");
        return;
    }

    // Copy text inside the Clipboard
    copyTextClipboard(orc_text);
});

/* Setup all copy button in tha table */
tableBtnCopy.forEach(button => {
    // Add click envent to each button
    button.addEventListener("click", () => {
        
        // Get the ID of the text element to copy from the data-clipbord_id attribute
        const textElementID = button.getAttribute("data-clipboard-id");
        
        // Get the text content of the element
        const textToCopy = document.getElementById(textElementID).textContent;

        // Copy the text to the clipboard
        copyTextClipboard(textToCopy);
    });
});


/* TO DO  1. about section for OCR with TensorFlow and API OCR */
/* And need a way to display text with out releading the page server */

/* Footer */
// Create a new Date object
const date = new Date()
// Get the footerDate element by its id
const footerDate = document.getElementById('footerDate');
// Populate the footerDate element with the current year
footerDate.innerHTML = `Projet cours CS50x &copy; Harvard University - ${date.getFullYear()}`;

