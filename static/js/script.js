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

                // TODO: For now in local storage, in the future will be sent to Flask backend
                const projectId = `project_${Date.now()}`;
                const projectData = { id: projectId, title, description };
                localStorage.setItem(projectId, JSON.stringify(projectData));

                // TODO: For now simulate this, in the future redirect and URL by backend
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
        const recommendationsContainer = document.getElementById('recommendationsContainer');

        if (titleDisplay) titleDisplay.textContent = projectData.title;
        if (descriptionDisplay) descriptionDisplay.textContent = projectData.description;
        if (document.title && titleDisplay) document.title = `Project: ${projectData.title}`;

        if (recommendationsContainer) {
            fetchRecommendations(projectData.title, projectData.description)
                .then(recommendations => {
                    renderRecommendations(recommendations, recommendationsContainer);
                })
                .catch(error => {
                    console.error("Error fetching recommendations:", error);
                    recommendationsContainer.innerHTML = '<p>Could not load recommendations at this time.</p>';
                });
        }
    };

    async function fetchRecommendations(projectDescription) {
        console.log(`Waiting on recommendations based on project description...`);
        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ projectDescription: projectDescription }),
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

    handleRouting();

    if (window.location.pathname.startsWith('/project/')) {
        const projectId = window.location.pathname.split('/').pop();
        loadProjectOverviewData(projectId);
    }
});
