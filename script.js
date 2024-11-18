
document.getElementById("enroll-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const studentName = document.getElementById("student-name").value;
    const studentImage = document.getElementById("student-image").files[0];

    const formData = new FormData();
    formData.append("name", studentName);
    formData.append("file", studentImage);

    try {
        const response = await fetch("http://localhost:8000/enroll/", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();
        if (response.ok) {
            alert(`${studentName} enrolled successfully!`);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error("Error during enrollment:", error);
        alert("There was an issue with the enrollment request.");
    }
});

async function startAttendance() {
    try {
        const response = await fetch("http://localhost:8000/start-attendance/", {
            method: "GET",
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
            document.getElementById("attendance-status").innerText = "Attendance started!";
            console.log(data.message);  
        } else {
            // Show the error message from the backend
            document.getElementById("attendance-status").innerText = data.message || "An error occurred.";
            console.error("Error:", data.message);  
        }
    } catch (error) {
        console.error("Error starting attendance:", error);
        document.getElementById("attendance-status").innerText = "Error starting attendance.";
    }
}

async function stopAttendance() {
    try {
        const response = await fetch("http://localhost:8000/stop-attendance/", {
            method: "GET",
        });

        const data = await response.json();

        // Check if response is successful
        if (response.ok && data.status === "success") {
            document.getElementById("attendance-status").innerText = "Attendance stopped.";
            console.log(data.message); 
        } else {
            // Show the error message from the backend
            document.getElementById("attendance-status").innerText = data.message || "An error occurred.";
            console.error("Error:", data.message);  
        }
    } catch (error) {
        // Handle any network or unexpected errors
        console.error("Error stopping attendance:", error);
        document.getElementById("attendance-status").innerText = "Error stopping attendance.";
    }
}
