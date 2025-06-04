document.addEventListener('DOMContentLoaded', () => {
    const handleRouting = () => {
        const path = window.location.pathname;

        if (path === '/create-project') {
           // Do nothing in this case for now
        } else if (path.startsWith('/project/')) {
            const projectId = path.split('/').pop();
            loadProjectOverviewData(projectId);
        } else if (path === '/') {
            const createProjectBtn = document.getElementById('createProjectBtn');
            if (createProjectBtn) {
                createProjectBtn.addEventListener('click', () => {
                    window.location.href = '/create-project';
                });
            }
        }

        const createProjectForm = document.getElementById('createProjectForm');
        if (createProjectForm) {
            createProjectForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const title = document.getElementById('projectTitle').value;
                const description = document.getElementById('projectDescription').value;
                const pdfFile = document.getElementById('pdfFile').files[0];
                const paperContext = document.getElementById('paperContext').value;

                // TODO: For now in local storage, in the future will be sent to Flask backend
                const projectId = `project_${Date.now()}`;
                const projectData = { id: projectId, title, description };
                localStorage.setItem(projectId, JSON.stringify(projectData));


                // If a PDF was uploaded, store the enhanced profile
                if (pdfFile && paperContext) {
                    const formData = new FormData();
                    formData.append('pdf', pdfFile);
                    formData.append('paperContext', paperContext);
                    formData.append('projectDescription', description);
                    const response = await fetch('/api/upload-paper', {
                        method: 'POST',
                        body: formData
                    });
                    if (response.ok) {
                        const enhancedProfile = await response.text();
                        localStorage.setItem(`${projectId}_enhancedProfile`, enhancedProfile);
                    }
                }

                window.location.href = `/project/${projectId}`;
            });
        }
    };

    const loadProjectOverviewData = (projectId) => {
        // TODO: For now use localStorage for the project data
        const projectDataString = localStorage.getItem(projectId);
        if (!projectDataString) {
            console.error("Project data not found for ID:", projectId);
            if (document.getElementById('projectTitleDisplay')) {
                 document.getElementById('projectTitleDisplay').textContent = "Project Not Found";
                 document.getElementById('projectDescriptionDisplay').textContent = "The project data could not be loaded.";
            }
            return;
        }

        const projectData = JSON.parse(projectDataString);

        const titleDisplay = document.getElementById('projectTitleDisplay');
        const descriptionDisplay = document.getElementById('projectDescriptionDisplay');
        const enhancedDescriptionDisplay = document.getElementById('enhancedDescriptionDisplay');
        const recommendationsContainer = document.getElementById('recommendationsContainer');

        if (titleDisplay) titleDisplay.textContent = projectData.title;
        if (descriptionDisplay) descriptionDisplay.textContent = projectData.description;
        if (document.title && titleDisplay) document.title = `Project: ${projectData.title}`;

        // Load enhanced description if it exists
        const enhancedProfile = localStorage.getItem(`${projectId}_enhancedProfile`);
        if (enhancedProfile && enhancedDescriptionDisplay) {
            // Replace newlines with <br> tags and preserve whitespace
            const formattedText = enhancedProfile
                .replace(/\n/g, '<br>')
                .replace(/\s{2,}/g, match => '&nbsp;'.repeat(match.length));
            enhancedDescriptionDisplay.innerHTML = `<p style="white-space: pre-wrap;">${formattedText}</p>`;
        }

        if (recommendationsContainer) {
            fetchRecommendations(projectData.description, enhancedProfile)
                .then(recommendations => {
                    renderRecommendations(recommendations, recommendationsContainer);
                })
                .catch(error => {
                    console.error("Error fetching recommendations:", error);
                    recommendationsContainer.innerHTML = '<p>Could not load recommendations at this time.</p>';
                });
        }

        // Add PDF upload form handler
        const paperUploadForm = document.getElementById('paperUploadForm');
        if (paperUploadForm) {
            paperUploadForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                
                const pdfFile = document.getElementById('pdfFile').files[0];
                const paperContext = document.getElementById('paperContext').value;
                
                if (!pdfFile || !paperContext) {
                    alert('Please provide both a PDF file and context about the paper.');
                    return;
                }
                
                const formData = new FormData();
                formData.append('pdf', pdfFile);
                formData.append('paperContext', paperContext);
                formData.append('projectDescription', projectData.description);
                
                try {
                    const response = await fetch('/api/upload-paper', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Failed to upload paper');
                    }
                    
                    const recommendations = await response.json();
                    renderRecommendations(recommendations, recommendationsContainer);
                    
                    // Clear the form
                    paperUploadForm.reset();
                    
                } catch (error) {
                    console.error('Error uploading paper:', error);
                    alert('Failed to upload paper: ' + error.message);
                }
            });
        }
    };

    async function fetchRecommendations(projectDescription, enhancedProfile) {
        console.log(`Waiting on recommendations based on project description...`);
        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    projectDescription: projectDescription,
                    enhancedProfile: enhancedProfile || ''
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}. Server said: ${errorData.error || 'No additional error info.'}`);
            }
            const recommendations = await response.json();
            return recommendations;

        } catch (error) {
            console.error('Failed to fetch recommendations:', error);
            throw error;
        }
    }

    function renderRecommendations(recommendations, container) {
        container.innerHTML = '';
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p>No recommendations available for this project yet.</p>';
            return;
        }

        recommendations.forEach(paper => {
            const card = document.createElement('div');
            card.classList.add('recommendation-card');

            const titleEl = document.createElement('h3');
            titleEl.textContent = paper.title;

            const linkEl = document.createElement('a');
            linkEl.href = paper.link;
            linkEl.textContent = "Read Paper";
            linkEl.target = "_blank";

            const descriptionEl = document.createElement('p');
            descriptionEl.textContent = paper.description;

            card.appendChild(titleEl);
            card.appendChild(linkEl);
            card.appendChild(descriptionEl);
            container.appendChild(card);
        });
    }

    // Add toggle function for enhanced description
    window.toggleEnhancedDescription = function() {
        const content = document.getElementById('enhancedDescriptionDisplay');
        const button = document.querySelector('.btn-toggle');
        if (content.classList.contains('hidden')) {
            content.classList.remove('hidden');
            button.textContent = 'Hide Enhanced Description';
        } else {
            content.classList.add('hidden');
            button.textContent = 'Show Enhanced Description';
        }
    };

    handleRouting();

});
