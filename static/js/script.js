document.addEventListener('DOMContentLoaded', () => {
    const handleRouting = () => {
        const path = window.location.pathname;

        if (path === '/create-project') {
           setupPDFUpload();
        } else if (path.startsWith('/project/')) {
            const projectId = path.split('/').pop();
            loadProjectOverviewData(projectId).catch(error => {
                console.error("Error loading project overview:", error);
            });
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

                try {
                    const response = await fetch('/api/createProject', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, prompt: description }),
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        alert(`Error creating project: ${errorData.error}`);
                        return;
                    }

                    const result = await response.json();
                    if (result.success) {
                        const projectId = result.project_id;
                        const projectData = { id: projectId, title, description };
                        localStorage.setItem(projectId, JSON.stringify(projectData));
                        window.location.href = `/project/${projectId}`;
                    } else {
                        alert('Failed to create project');
                    }
                } catch (error) {
                    console.error('Error creating project:', error);
                    alert('Failed to create project. Please try again.');
                }
            });
        }
    };

    function setupPDFUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('paperUpload');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const removeBtn = document.getElementById('removeFile');
        if (!uploadArea || !fileInput) return;

        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelection(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleFileSelection(file);
            }
        });

        removeBtn?.addEventListener('click', () => {
            removeFile();
        });

        function handleFileSelection(file) {
            if (file.type !== 'application/pdf') {
                alert('Please select a PDF file only.');
                return;
            }

            const maxSize = 50 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('File size must be less than 50MB.');
                return;
            }

            displayFileInfo(file);
        }

        function displayFileInfo(file) {
            const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);

            fileName.textContent = file.name;
            fileSize.textContent = `${sizeInMB} MB`;

            uploadArea.style.display = 'none';
            fileInfo.style.display = 'flex';

            extractPDFText(file);
        }

        async function extractPDFText(file) {
            const projectDescription = document.getElementById('projectDescription');
            if (!projectDescription) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const originalValue = projectDescription.value;
                projectDescription.value = originalValue + '\n\n[Extracting PDF text...]';

                const response = await fetch('/api/extract-pdf-text', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    try {
                        const result = await response.json();
                        alert(`Error extracting PDF text: ${result.error}`);
                    } catch (jsonError) {
                        alert(`Error extracting PDF text: HTTP ${response.status} - ${response.statusText}`);
                    }
                    projectDescription.value = originalValue;
                    return;
                }

                const result = await response.json();

                if (result.success) {
                    const currentText = originalValue.trim();
                    const newText = currentText ?
                        `${currentText}\n\n${result.extracted_text}` :
                        result.extracted_text;
                    projectDescription.value = newText;
                } else {
                    projectDescription.value = originalValue;
                    alert(`Error extracting PDF text: ${result.error}`);
                }
            } catch (error) {
                projectDescription.value = projectDescription.value.replace('\n\n[Extracting PDF text...]', '');
                alert(`Failed to extract PDF text: ${error.message}`);
            }
        }

        function removeFile() {
            fileInput.value = '';

            fileInfo.style.display = 'none';
            uploadArea.style.display = 'block';

            fileName.textContent = '';
            fileSize.textContent = '';
        }
    }

    const loadProjectOverviewData = async (projectId) => {
        try {
            // Try to get project data from backend first
            const response = await fetch('/api/getProjects');
            const data = await response.json();

            let projectData = null;
            if (data.success && data.projects) {
                projectData = data.projects.find(p => p.project_id === projectId);
            }

            // Turn to localStorage if not found in backend
            if (!projectData) {
                const projectDataString = localStorage.getItem(projectId);
                if (projectDataString) {
                    projectData = JSON.parse(projectDataString);
                }
            }

            if (!projectData) {
                console.error("Project data not found for ID:", projectId);
                if (document.getElementById('projectTitleDisplay')) {
                     document.getElementById('projectTitleDisplay').textContent = "Project Not Found";
                     document.getElementById('projectDescriptionDisplay').textContent = "The project data could not be loaded.";
                }
                return;
            }

        const titleDisplay = document.getElementById('projectTitleDisplay');
        const descriptionDisplay = document.getElementById('projectDescriptionDisplay');
        const recommendationsContainer = document.getElementById('recommendationsContainer');
        const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');

        // Handle both backend and localStorage data structures
        const title = projectData.title || projectData.name || 'Untitled Project';
        const description = projectData.description || 'No description available';

        if (titleDisplay) titleDisplay.textContent = title;
        if (descriptionDisplay) {
            descriptionDisplay.textContent = description;
            setupCollapsibleDescription(description);
        }
        if (document.title && titleDisplay) document.title = `Project: ${title}`;

        if (recommendationsContainer && agentThoughtsContainer) {
            // Set initial state messages
            agentThoughtsContainer.innerHTML = '<p>🧠 Agent is thinking...</p>';
            recommendationsContainer.innerHTML = '<p>⌛ Waiting for agent to provide recommendations...</p>';

            fetchRecommendationsStream(projectId, agentThoughtsContainer, recommendationsContainer)
                .catch(error => {
                    console.error("Error fetching recommendations stream:", error);
                    agentThoughtsContainer.innerHTML += '<p>❌ Error communicating with the agent.</p>';
                    recommendationsContainer.innerHTML = '<p>Could not load recommendations at this time.</p>';
                });
        }
    } catch (error) {
        console.error("Error loading project data:", error);
        if (document.getElementById('projectTitleDisplay')) {
            document.getElementById('projectTitleDisplay').textContent = "Error Loading Project";
            document.getElementById('projectDescriptionDisplay').textContent = "There was an error loading the project data.";
        }
    }
};

    async function fetchRecommendationsStream(projectId, thoughtsContainer, recommendationsContainer) {
        console.log(`Starting to stream recommendations for project ID: ${projectId}`);
        if (thoughtsContainer) {
            thoughtsContainer.innerHTML = ''; // Clear for new thoughts
        }

        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    update_recommendations: true  // Always fetch papers for new projects
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Network response was not ok: ${response.status}. ${errorText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep incomplete message in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonString = line.substring(6);
                        const data = JSON.parse(jsonString);

                        if (data.thought) {
                            const thoughtEl = document.createElement('li');

                            let content = data.thought;
                            let icon = '🧠';
                            if (content.startsWith('Calling tool:')) {
                                icon = '🛠️';
                                content = content.replace('Calling tool:', '<strong>Calling tool:</strong>');
                            } else if (content.startsWith('Tool response received:')) {
                                icon = '✅';
                                content = `<p>${content.replace('Tool response received:', '<strong>Tool response received:</strong>')}</p>`;
                            } else if (content.startsWith('Receiving user input')) {
                                icon = '👤';
                            } else if (content.startsWith('Final response')) {
                                icon = '🏁';
                            }

                            thoughtEl.innerHTML = `${icon} ${content}`;
                            if (thoughtsContainer) {
                                thoughtsContainer.appendChild(thoughtEl);
                                thoughtsContainer.scrollTop = thoughtsContainer.scrollHeight;
                            }
                        } else if (data.recommendations) {
                            renderRecommendations(data.recommendations, recommendationsContainer);
                        } else if (data.error) {
                            console.error('Server-side error:', data.error);
                            recommendationsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
                            if (thoughtsContainer) {
                                thoughtsContainer.innerHTML += `<p>❌ An error occurred.</p>`;
                            }
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Failed to fetch recommendations stream:', error);
            throw error;
        }
    }

    function renderRecommendations(recommendations, container) {
        container.innerHTML = '';
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p>No recommendations available for this project yet.</p>';
            return;
        }

        recommendations.forEach((paper, index) => {
            const card = document.createElement('div');
            card.classList.add('recommendation-card');

            // Add temporary highlight for replacement papers
            if (paper.is_replacement) {
                card.classList.add('new-replacement');
                // Remove the highlight after 5 seconds
                setTimeout(() => {
                    card.classList.remove('new-replacement');
                }, 5000);
            }

            const titleEl = document.createElement('h3');
            titleEl.textContent = paper.title;

            const linkEl = document.createElement('a');
            linkEl.href = paper.link;
            linkEl.textContent = "Read Paper";
            linkEl.target = "_blank";

            const descriptionEl = document.createElement('p');
            descriptionEl.textContent = paper.description;

            const starRatingEl = document.createElement('div');
            starRatingEl.classList.add('star-rating');
            starRatingEl.innerHTML = `
                <span class="star" data-value="1">&#9733;</span>
                <span class="star" data-value="2">&#9733;</span>
                <span class="star" data-value="3">&#9733;</span>
                <span class="star" data-value="4">&#9733;</span>
                <span class="star" data-value="5">&#9733;</span>
            `;

            card.dataset.paperHash = paper.hash;

            card.appendChild(titleEl);
            card.appendChild(linkEl);
            card.appendChild(descriptionEl);
            card.appendChild(starRatingEl);

            container.appendChild(card);
        });
    }

    function setupCollapsibleDescription(description) {
        const descriptionDisplay = document.getElementById('projectDescriptionDisplay');
        const descriptionWrapper = descriptionDisplay?.parentElement;
        const toggleButton = document.getElementById('descriptionToggle');
        const fadeOverlay = document.getElementById('descriptionFadeOverlay');
        const controls = document.getElementById('descriptionControls');
        const expandText = toggleButton?.querySelector('.expand-text');

        if (!descriptionDisplay || !descriptionWrapper || !toggleButton || !fadeOverlay || !controls || !expandText) return;

        const wordCount = description.trim().split(/\s+/).length;

        if (wordCount > 500) {
            const isCollapsed = true;

            descriptionDisplay.classList.toggle('collapsed', isCollapsed);
            descriptionDisplay.classList.toggle('expanded', !isCollapsed);
            toggleButton.classList.toggle('expanded', !isCollapsed);
            fadeOverlay.classList.toggle('visible', isCollapsed);
            controls.classList.add('visible');

            expandText.textContent = isCollapsed ? 'Show full description' : 'Hide full description';

            toggleButton.addEventListener('click', () => {
                const currentlyCollapsed = descriptionDisplay.classList.contains('collapsed');

                descriptionDisplay.classList.toggle('collapsed', !currentlyCollapsed);
                descriptionDisplay.classList.toggle('expanded', currentlyCollapsed);
                toggleButton.classList.toggle('expanded', currentlyCollapsed);
                fadeOverlay.classList.toggle('visible', !currentlyCollapsed);

                expandText.textContent = !currentlyCollapsed ? 'Show full description' : 'Hide full description';
            });
        } else {
            // Short description, no need to use expandable view
            descriptionDisplay.classList.add('expanded');
            fadeOverlay.classList.remove('visible');
            controls.classList.remove('visible');
        }
    }

    // --- HOMEPAGE PROJECTS & SEARCH ---
    async function loadProjectsFromAPI() {
        try {
            const response = await fetch('/api/getProjects');
            const data = await response.json();
            if (data.success && data.projects) {
                return data.projects;
            } else {
                console.error('Failed to load projects:', data.error);
                return [];
            }
        } catch (error) {
            console.error('Error fetching projects:', error);
            return [];
        }
    }

    function renderProjects(projects) {
        const projectsList = document.getElementById('projectsList');
        if (!projectsList) return;
        projectsList.innerHTML = '';
        projects.forEach((project, idx) => {
            const card = document.createElement('div');
            card.className = 'project-card';
            card.style.animationDelay = `${idx * 0.04 + 0.1}s`;
            card.innerHTML = `
                <div class="project-title">${project.name}</div>
                <div class="project-description">${project.description}</div>
                <div class="project-tags">
                    ${project.tags.map(tag => `<span class="project-tag">${tag}</span>`).join(' ')}
                </div>
                <div class="project-date">Created: ${project.date}</div>
            `;
            // Navigate to project page on click
            card.addEventListener('click', () => {
                if (project.project_id) {
                    window.location.href = `/project/${project.project_id}`;
                } else {
                    // Fallback animation if no project_id
                    card.classList.add('card-clicked');
                    setTimeout(() => card.classList.remove('card-clicked'), 400);
                }
            });
            projectsList.appendChild(card);
        });
        animateCardsOnScroll();
    }

    function filterProjectsBySearch(projects, searchValue) {
        const val = searchValue.trim().toLowerCase();
        if (!val) return projects;
        return projects.filter(p =>
            p.name.toLowerCase().includes(val) ||
            p.description.toLowerCase().includes(val) ||
            p.tags.some(tag => tag.toLowerCase().includes(val))
        );
    }

    function animateCardsOnScroll() {
        const cards = document.querySelectorAll('.project-card');
        const observer = new window.IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = 1;
                    entry.target.style.transform = 'translateY(0) scale(1)';
                }
            });
        }, { threshold: 0.12 });
        cards.forEach(card => {
            card.style.opacity = 0;
            card.style.transform = 'translateY(40px) scale(0.98)';
            observer.observe(card);
        });
    }

    // On DOMContentLoaded, render projects and set up search
    if (window.location.pathname === '/') {
        let allProjects = [];

        // Load projects from API
        loadProjectsFromAPI().then(projects => {
            allProjects = projects;
            renderProjects(allProjects);
        });

        const searchInput = document.getElementById('projectSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const filtered = filterProjectsBySearch(allProjects, e.target.value);
                renderProjects(filtered);
            });
        }
        // Animate cards on scroll (again, in case of resize/search)
        window.addEventListener('resize', animateCardsOnScroll);
        window.addEventListener('scroll', animateCardsOnScroll);
    }

    handleRouting();

    // Star rating handlers
    const recommendationsContainer = document.getElementById('recommendationsContainer');
    if (recommendationsContainer) {
        recommendationsContainer.addEventListener('mouseover', function (e) {
            if (e.target.classList.contains('star')) {
                const value = parseInt(e.target.dataset.value);
                const stars = Array.from(e.target.parentNode.querySelectorAll('.star'));
                stars.forEach(star => {
                    star.classList.toggle('hovered', parseInt(star.dataset.value) <= value);
                });
            }
        });

        recommendationsContainer.addEventListener('mouseout', function (e) {
            if (e.target.classList.contains('star')) {
                const stars = Array.from(e.target.parentNode.querySelectorAll('.star'));
                stars.forEach(star => {
                    star.classList.remove('hovered');
                });
            }
        });

       recommendationsContainer.addEventListener('click', function (e) {
    if (e.target.classList.contains('star')) {
        const clickedStar = e.target;
        const stars = Array.from(clickedStar.parentNode.querySelectorAll('.star'));
        const value = parseInt(clickedStar.dataset.value);

        stars.forEach(star => {
            star.classList.toggle('selected', parseInt(star.dataset.value) <= value);
        });

        console.log(`Rated ${value} star(s)`);

        // Get paper hash (you should include it when rendering each recommendation card)
        const paperHash = clickedStar.closest('.recommendation-card').dataset.paperHash;
        const currentProjectId = window.location.pathname.split('/').pop();

        console.log(`Sending rating - paperHash: ${paperHash}, projectId: ${currentProjectId}, rating: ${value}`);

        // For low ratings, remember the card position for replacement
        let cardToReplace = null;
        let cardIndex = -1;
        if (value <= 2) {
            cardToReplace = clickedStar.closest('.recommendation-card');
            const allCards = Array.from(document.querySelectorAll('.recommendation-card'));
            cardIndex = allCards.indexOf(cardToReplace);

            // Keep the space occupied but make it invisible
            cardToReplace.style.opacity = '0';
            cardToReplace.style.visibility = 'hidden';
            // Use position absolute to take it out of flow but keep space with a placeholder
            const originalHeight = cardToReplace.offsetHeight;
            cardToReplace.style.position = 'absolute';
            cardToReplace.style.zIndex = '-1';

            // Create a placeholder div to maintain the space
            const placeholder = document.createElement('div');
            placeholder.style.height = originalHeight + 'px';
            placeholder.style.width = '100%';
            placeholder.style.flexShrink = '0';
            placeholder.classList.add('replacement-placeholder');
            cardToReplace.parentNode.insertBefore(placeholder, cardToReplace);
        }

        // Save the rating
        fetch('/api/rate_paper', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_hash: paperHash, rating: value, project_id: currentProjectId  })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                console.log("Rating saved!");

                // Check if a replacement was performed
                if (data.replacement && data.replacement.status === 'success') {
                    console.log("Paper replaced successfully:", data.replacement);

                    // Show popup notification with the new paper name
                    const replacementDetails = data.replacement;
                    if (replacementDetails.replacement_title) {
                        showReplacementNotification(replacementDetails.replacement_title);
                    }

                    // Insert the replacement paper at the exact same position
                    if (cardIndex >= 0 && replacementDetails.replacement_title) {
                        insertReplacementPaper(replacementDetails, cardIndex, recommendationsContainer);
                    } else {
                        // Fallback: refresh all recommendations
                        refreshRecommendations(recommendationsContainer, currentProjectId);
                    }
                } else if (value <= 2) {
                    console.log("Low rating detected but no replacement was performed.");
                }
            } else {
                console.error("Failed to save rating:", data.message);
            }
        })
        .catch(err => {
            console.error("Error in rating process:", err);
            // Show the card again on error
            if (cardToReplace) {
                cardToReplace.style.opacity = '1';
                cardToReplace.style.transform = 'scale(1)';
                cardToReplace.style.display = 'block';
            }
        });
    }
});

    }
});


// Function to show replacement notification popup
function showReplacementNotification(newPaperTitle) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'replacement-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">🔄</div>
            <div class="notification-text">
                <div class="notification-title">Paper Replaced!</div>
                <div class="notification-message">Added: "${newPaperTitle}"</div>
            </div>
        </div>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    // Remove after 4 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// Function to insert replacement paper at specific position
function insertReplacementPaper(replacementDetails, position, container) {
    // Find the invisible card at the specified position
    const allCards = Array.from(container.querySelectorAll('.recommendation-card'));
    const invisibleCard = allCards[position];

    if (invisibleCard && invisibleCard.style.visibility === 'hidden') {
        // Remove the placeholder first
        const placeholder = container.querySelector('.replacement-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        // Replace the invisible card's content
        invisibleCard.dataset.paperHash = replacementDetails.replacement_paper_hash;
        invisibleCard.classList.add('new-replacement');

        invisibleCard.innerHTML = `
            <h3>${replacementDetails.replacement_title}</h3>
            <a href="${replacementDetails.replacement_url}" target="_blank">Read Paper</a>
            <p>${replacementDetails.replacement_summary}</p>
            <div class="star-rating">
                <span class="star" data-value="1">&#9733;</span>
                <span class="star" data-value="2">&#9733;</span>
                <span class="star" data-value="3">&#9733;</span>
                <span class="star" data-value="4">&#9733;</span>
                <span class="star" data-value="5">&#9733;</span>
            </div>
        `;

        // Reset the card's styling and animate it in
        invisibleCard.style.visibility = 'visible';
        invisibleCard.style.opacity = '0';
        invisibleCard.style.transform = 'scale(0.8)';
        invisibleCard.style.position = '';
        invisibleCard.style.zIndex = '';

        setTimeout(() => {
            invisibleCard.style.opacity = '1';
            invisibleCard.style.transform = 'scale(1)';
        }, 100);

        // Remove highlight after 3 seconds
        setTimeout(() => {
            invisibleCard.classList.remove('new-replacement');
        }, 3000);
    }
}
