// ←← PUBSUB UI HELPERS: Definitions first ←←
//renderPubSubSection clears out the <div id="pubsubPapersContainer">
function renderPubSubSection() {
    document.getElementById('pubsubPapersContainer').innerHTML = '';
}

//setupPubSubForm wires up Subscribe form.
function setupPubSubForm() {
    const form = document.getElementById('pubsubSubscribeForm');
    if (!form) return;        // if there is no pubsubSubscribeForm, exit
    const emailInput = document.getElementById('pubsubEmail');
    form.addEventListener('submit', e => {
      e.preventDefault();
      alert(`Thanks for subscribing, ${emailInput.value}!`);
      emailInput.value = '';
    });
}
//renderPubSubPapers turns an array of paper objects into cards.
function renderPubSubPapers(papers, container) {
    container.innerHTML = '';
    papers.forEach(paper => {
      // 1) create card's div
      const card = document.createElement('div');
      card.classList.add('recommendation-card');

      // 2) create and fill out h3 from title (match Recommendations section)
      const titleEl = document.createElement('h3');
      titleEl.textContent = paper.title;

      // 3) creates link
      const linkEl = document.createElement('a');
      linkEl.href = paper.link;
      linkEl.textContent = "Read Paper";
      linkEl.target = "_blank";

      // 4) creates paragraph for description
      const descriptionEl = document.createElement('p');
      descriptionEl.textContent = paper.description;

      // 5) ensambles all in card
      card.appendChild(titleEl);
      card.appendChild(linkEl);
      card.appendChild(descriptionEl);
      container.appendChild(card);
    });
}


    async function handleRouting () {
        const path = window.location.pathname;

        if (path === '/create-project') {
           setupPDFUpload();

           const createProjectForm = document.getElementById('createProjectForm');
           createProjectForm?.addEventListener('submit', async(event) => {
            event.preventDefault();
            const title       = document.getElementById('projectTitle').value;
            const description = document.getElementById('projectDescription').value;

            // POST to real endpoint instead of localStorage
            const res = await fetch('/api/projects', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ title, description })
            });
            if (!res.ok) {
              return alert('Error creating project');
            }
            const { projectId } = await res.json();
            window.location.href = `/project/${projectId}?updateRecommendations=true`;
          });


        } else if (path.startsWith('/project/')) {
            const projectId = path.split('/').pop();
            // 1Fetch the title/description/queries from Flask (real metadata from project)
            const projectRes = await fetch (`/api/project/${projectId}`)
            if (!projectRes.ok) {
                // if fails, shows error UI and goes out
                document.getElementById('projectTitleDisplay').textContent = 'Project Not Found';
                return;
            }
            const project = await projectRes.json();
            // Populate header
            document.getElementById('projectTitleDisplay').textContent = project.title;
            document.getElementById('projectDescriptionDisplay').textContent = project.description;
            //To not depending on localStorage for title and description:
            document.title = `Project: ${project.title}`;
            setupCollapsibleDescription(project.description);

            const container = document.getElementById('pubsubPapersContainer');

            renderPubSubSection();
            setupPubSubForm();

            const params= new URLSearchParams(window.location.search);
            const updateRecommendations = params.get('updateRecommendations') === 'true';
            loadProjectOverviewData(projectId, project.description, updateRecommendations);
            if (updateRecommendations) {
                history.replaceState({}, '', window.location.pathname);
            }

            try {
                //todo update newsletter papers only on project creation or once a week
                const updateRes = await fetch('/api/pubsub/update_newsletter_papers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ projectId })
                });
                const updateJson = await updateRes.json();
                if (!updateRes.ok) {
                  console.warn('⚠️ update_newsletter_papers status failed:', updateRes.status, updateJson);
                }
              } catch (err) {
                console.error('Error when calling update_newsletter_papers:', err);
              }
                const papers = await fetch(
                    `/api/pubsub/get_newsletter_papers?projectId=${projectId}`
                ).then(r => r.json());
                console.log('PubSub papers fetched:', papers);
                console.log('pubsubPapersContainer is', container);
            if (papers.length === 0) {
                // Instead of rendering test cards, show a placeholder message
                container.innerHTML = '<p class="no-papers-placeholder">Here the newest papers will be shown later.</p>';
            } else {
                console.log('📬 Rendering real PubSub papers:', papers);
                renderPubSubPapers(papers, container);
            }


        } else if (path === '/') {
            const createProjectBtn = document.getElementById('createProjectBtn');
            if (createProjectBtn) {
                createProjectBtn.addEventListener('click', () => {
                    window.location.href = '/create-project';
                });
            }
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

    function loadProjectOverviewData (projectId, projectDescription,  updateRecommendations = false) {
        const recommendationsContainer = document.getElementById('recommendationsContainer');
        const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');

            // Set initial state messages
            agentThoughtsContainer.innerHTML = '<p>🧠 Agent is thinking...</p>';
            recommendationsContainer.innerHTML = '<p>⌛ Waiting for agent to provide recommendations...</p>';

            fetchRecommendationsStream(projectId, projectDescription, agentThoughtsContainer, recommendationsContainer, updateRecommendations)
                .catch(error => {
                    console.error("Error fetching recommendations stream:", error);
                    agentThoughtsContainer.innerHTML += '<p>❌ Error communicating with the agent.</p>';
                    recommendationsContainer.innerHTML = '<p>Could not load recommendations at this time.</p>';
                });
        }

    async function fetchRecommendationsStream(projectId, projectDescription, thoughtsContainer, recommendationsContainer,  updateRecommendations = false) {
        console.log(`Starting to stream recommendations based on project description...`);
        thoughtsContainer.innerHTML = ''; // Clear for new thoughts

        // Track the last thought element for subunit rendering
        let lastThoughtEl = null;

        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectId: projectId,
                    update_recommendations : updateRecommendations //todo set this to true only if new project or if future 'refresh recommendations' button pressed
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
                            thoughtsContainer.appendChild(thoughtEl);
                            thoughtsContainer.scrollTop = thoughtsContainer.scrollHeight;
                            lastThoughtEl = thoughtEl;
                        } else if (data.recommendations) {
                            renderRecommendations(data.recommendations, recommendationsContainer);
                        } else if (data.out_of_scope) {
                            // Render out-of-scope as a subunit under the last agent thought
                            renderOutOfScopeInThoughts(data.out_of_scope, lastThoughtEl, thoughtsContainer);
                            // Clear recommendations section
                            recommendationsContainer.innerHTML = '';
                        } else if (data.no_results) {
                            // Render no-results as a subunit under the last agent thought
                            renderNoResultsInThoughts(data.no_results, lastThoughtEl, thoughtsContainer);
                            // Clear recommendations section
                            recommendationsContainer.innerHTML = '';
                        } else if (data.error) {
                            console.error('Server-side error:', data.error);
                            recommendationsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
                            thoughtsContainer.innerHTML += `<p>❌ An error occurred.</p>`;
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

    // Render out-of-scope as a subunit under the last agent thought
    function renderOutOfScopeInThoughts(outOfScopeData, lastThoughtEl, thoughtsContainer) {
        const message = outOfScopeData.message;
        // Create out-of-scope subunit
        const subunit = document.createElement('div');
        subunit.classList.add('out-of-scope-thought-subunit');

        // Short explanation (top)
        const shortEl = document.createElement('div');
        shortEl.classList.add('out-of-scope-short');
        shortEl.textContent = message.short_explanation;
        subunit.appendChild(shortEl);

        // Show details button (now below short explanation)
        const expandBtn = document.createElement('button');
        expandBtn.classList.add('out-of-scope-expand-btn');
        expandBtn.textContent = 'Show details';
        subunit.appendChild(expandBtn);

        // Expand/collapse for full explanation
        const fullEl = document.createElement('div');
        fullEl.classList.add('out-of-scope-full');
        fullEl.textContent = message.explanation;
        fullEl.style.display = 'none';
        expandBtn.addEventListener('click', () => {
            if (fullEl.style.display === 'none') {
                fullEl.style.display = 'block';
                expandBtn.textContent = 'Hide details';
            } else {
                fullEl.style.display = 'none';
                expandBtn.textContent = 'Show details';
            }
        });
        subunit.appendChild(fullEl);

        // Suggestion
        const suggestionEl = document.createElement('div');
        suggestionEl.classList.add('out-of-scope-suggestion-inline');
        suggestionEl.innerHTML = `<strong>Suggestion:</strong> ${message.suggestion}`;
        subunit.appendChild(suggestionEl);

        // New query input
        const inputContainer = document.createElement('div');
        inputContainer.classList.add('new-query-inline-container');
        const inputLabel = document.createElement('label');
        inputLabel.textContent = 'Please provide a new query:';
        inputLabel.setAttribute('for', 'newQueryInput');
        const inputEl = document.createElement('textarea');
        inputEl.id = 'newQueryInput';
        inputEl.placeholder = 'Enter a new research query focused on academic topics, technologies, or fields of study...';
        inputEl.rows = 3;
        const submitBtn = document.createElement('button');
        submitBtn.textContent = 'Submit New Query';
        submitBtn.classList.add('btn', 'btn-primary');
        submitBtn.addEventListener('click', () => {
            const newQuery = inputEl.value.trim();
            if (newQuery) {
                // Remove the subunit and restart
                if (subunit.parentNode) subunit.parentNode.removeChild(subunit);
                thoughtsContainer.innerHTML = '<p>🧠 Processing new query...</p>';
                // Update the top input field to reflect the new query
                const topInput = document.querySelector('input#projectTitle, textarea#projectDescription, input[type="text"], textarea');
                if (topInput) {
                    topInput.value = newQuery;
                }
                // Start new recommendation stream with the new query
                const recommendationsContainer = document.getElementById('recommendationsContainer');
                fetchRecommendationsStream(newQuery, thoughtsContainer, recommendationsContainer)
                    .catch(error => {
                        console.error("Error fetching recommendations for new query:", error);
                        thoughtsContainer.innerHTML += '<p>❌ Error processing new query.</p>';
                    });
            } else {
                alert('Please enter a new query.');
            }
        });
        inputContainer.appendChild(inputLabel);
        inputContainer.appendChild(inputEl);
        inputContainer.appendChild(submitBtn);
        subunit.appendChild(inputContainer);

        // Insert subunit under the last thought or at the end
        if (lastThoughtEl) {
            lastThoughtEl.appendChild(subunit);
        } else {
            thoughtsContainer.appendChild(subunit);
        }
    }

    // Render no-results as a subunit under the last agent thought
    function renderNoResultsInThoughts(noResultsData, lastThoughtEl, thoughtsContainer) {
        const message = noResultsData.message;

        // Create no-results subunit
        const subunit = document.createElement('div');
        subunit.classList.add('no-results-thought-subunit');

        // Explanation (top)
        const explanationEl = document.createElement('div');
        explanationEl.classList.add('no-results-explanation');
        explanationEl.innerHTML = message.explanation;
        subunit.appendChild(explanationEl);

        // Show filter details button
        const expandBtn = document.createElement('button');
        expandBtn.classList.add('no-results-expand-btn');
        expandBtn.textContent = 'Show filter details';
        subunit.appendChild(expandBtn);

        // Expand/collapse for filter details
        const filterDetailsEl = document.createElement('div');
        filterDetailsEl.classList.add('no-results-filter-details');
        filterDetailsEl.style.display = 'none';

        // Build filter details content
        let filterDetailsContent = '<h4>Applied Filters:</h4><ul>';
        if (message.filter_criteria) {
            Object.entries(message.filter_criteria).forEach(([key, value]) => {
                const operator = value.op || '=';
                filterDetailsContent += `<li><strong>${key}:</strong> ${operator} ${value.value}</li>`;
            });
        }
        filterDetailsContent += '</ul>';

        if (message.closest_values && Object.keys(message.closest_values).length > 0) {
            filterDetailsContent += '<h4>Closest Available Values:</h4><ul>';
            Object.entries(message.closest_values).forEach(([key, value]) => {
                const direction = value.direction || 'unknown';
                filterDetailsContent += `<li><strong>${key}:</strong> ${value.value} (${direction})</li>`;
            });
            filterDetailsContent += '</ul>';
        }

        filterDetailsEl.innerHTML = filterDetailsContent;

        expandBtn.addEventListener('click', () => {
            if (filterDetailsEl.style.display === 'none') {
                filterDetailsEl.style.display = 'block';
                expandBtn.textContent = 'Hide filter details';
            } else {
                filterDetailsEl.style.display = 'none';
                expandBtn.textContent = 'Show filter details';
            }
        });
        subunit.appendChild(filterDetailsEl);

        // Suggestion for new query
        const suggestionEl = document.createElement('div');
        suggestionEl.classList.add('no-results-suggestion-inline');
        suggestionEl.innerHTML = '<strong>💡 Tip:</strong> Try adjusting your filters or broadening your search terms.';
        subunit.appendChild(suggestionEl);

        // New query input
        const inputContainer = document.createElement('div');
        inputContainer.classList.add('new-query-inline-container');
        const inputLabel = document.createElement('label');
        inputLabel.textContent = 'Try a new search:';
        inputLabel.setAttribute('for', 'newQueryInput');
        const inputEl = document.createElement('textarea');
        inputEl.id = 'newQueryInput';
        inputEl.placeholder = 'Enter a new research query with different filters or broader terms...';
        inputEl.rows = 3;
        const submitBtn = document.createElement('button');
        submitBtn.textContent = 'Submit New Query';
        submitBtn.classList.add('btn', 'btn-primary');
        submitBtn.addEventListener('click', () => {
            const newQuery = inputEl.value.trim();
            if (newQuery) {
                // Remove the subunit and restart
                if (subunit.parentNode) subunit.parentNode.removeChild(subunit);
                thoughtsContainer.innerHTML = '<p>🧠 Processing new query...</p>';
                // Update the top input field to reflect the new query
                const topInput = document.querySelector('input#projectTitle, textarea#projectDescription, input[type="text"], textarea');
                if (topInput) {
                    topInput.value = newQuery;
                }
                // Start new recommendation stream with the new query
                const recommendationsContainer = document.getElementById('recommendationsContainer');
                fetchRecommendationsStream(newQuery, thoughtsContainer, recommendationsContainer)
                    .catch(error => {
                        console.error("Error fetching recommendations for new query:", error);
                        thoughtsContainer.innerHTML += '<p>❌ Error processing new query.</p>';
                    });
            } else {
                alert('Please enter a new query.');
            }
        });
        inputContainer.appendChild(inputLabel);
        inputContainer.appendChild(inputEl);
        inputContainer.appendChild(submitBtn);
        subunit.appendChild(inputContainer);

        // Insert subunit under the last thought or at the end
        if (lastThoughtEl) {
            lastThoughtEl.appendChild(subunit);
        } else {
            thoughtsContainer.appendChild(subunit);
        }
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
    document.addEventListener('DOMContentLoaded', () => {
    setupPubSubForm();

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
            // Truncate description to 120 chars for safety
            const truncatedDescription = truncateText(project.description, 120);
            card.innerHTML = `
                <div class="project-title">${project.title}</div>
                <div class="project-description">${truncatedDescription}</div>
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

    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.slice(0, maxLength - 3).trim() + '...';
    }

    function filterProjectsBySearch(projects, searchValue) {
        const val = searchValue.trim().toLowerCase();
        if (!val) return projects;
        return projects.filter(p =>
            (p.title && typeof p.title === 'string' && p.title.toLowerCase().includes(val)) ||
            (p.description && typeof p.description === 'string' && p.description.toLowerCase().includes(val)) ||
            (Array.isArray(p.tags) && p.tags.some(tag => tag && typeof tag === 'string' && tag.toLowerCase().includes(val)))
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
});
