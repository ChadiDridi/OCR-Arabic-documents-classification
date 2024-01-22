document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const predictionText = document.getElementById('prediction-text');
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        fetch('/insert', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())  // Parse JSON response
        .then(data => {
            predictionText.innerHTML = `<strong>Categorie de label:</strong> ${data.label}`;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
