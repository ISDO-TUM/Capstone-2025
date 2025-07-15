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
      card.classList.add('recommendation-card', 'pubsub-card');

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

// Helper function to create star rating HTML
const createStarRatingHTML = () => `
    <span class="star" data-value="1">&#9733;</span>
    <span class="star" data-value="2">&#9733;</span>
    <span class="star" data-value="3">&#9733;</span>
    <span class="star" data-value="4">&#9733;</span>
    <span class="star" data-value="5">&#9733;</span>
`;

// Helper function to show notification popup
const showNotification = (icon, title, message) => {
    const notification = document.createElement('div');
    notification.className = 'replacement-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">${icon}</div>
            <div class="notification-text">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => notification.classList.add('show'), 100);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
};

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
                // Show user-friendly message for new projects
                if (updateJson.error && updateJson.error.includes('No search queries found')) {
                console.log('📝 New project detected - queries will be generated when recommendations are created');
                }
            } else {
                // Add a small delay to ensure database transaction is committed
                console.log('✅ PubSub update completed successfully, waiting for database commit...');
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        } catch (err) {
            console.error('Error when calling update_newsletter_papers:', err);
        }
        const papers = await fetch(
            `/api/pubsub/get_newsletter_papers?projectId=${projectId}`
        ).then(r => {
            console.log('📡 PubSub papers response status:', r.status);
            return r.json();
        }).catch(err => {
            console.error('❌ Error fetching PubSub papers:', err);
            return [];
        });
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

        setupLoadMoreButton(projectId, recommendationsContainer, agentThoughtsContainer);
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

        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectId: projectId,
                    update_recommendations : updateRecommendations //set this to true only if new project or if future 'refresh recommendations' button pressed
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
                    } else if (data.recommendations) {
                        renderRecommendations(data.recommendations, recommendationsContainer);
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

function createPaperCard(paper) {
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
    starRatingEl.innerHTML = createStarRatingHTML();

    card.dataset.paperHash = paper.hash;
    card.dataset.title = paper.title.toLowerCase();
    card.dataset.rating = paper.rating || 0;

    card.appendChild(titleEl);
    card.appendChild(linkEl);
    card.appendChild(descriptionEl);
    card.appendChild(starRatingEl);

    return card;
}

function renderRecommendations(recommendations, container) {
    container.innerHTML = '';
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p>No recommendations available for this project yet.</p>';
        return;
    }

    window.currentRecommendations = recommendations;
    window.currentDisplayCount = recommendations.length;
    window.originalCardOrder = [];

    const papersToShow = recommendations.slice(0, window.currentDisplayCount);

    papersToShow.forEach((paper) => {
        const card = createPaperCard(paper);
        container.appendChild(card);
        window.originalCardOrder.push(card);
    });

    showLoadMoreButton();
    showSearchPanel();
    setupSearchPanel();

    setTimeout(() => {
        if (typeof filterAndSortPapers === 'function') {
            filterAndSortPapers();
        }
    }, 100);
}

async function loadMorePapers(projectId, recommendationsContainer, thoughtsContainer) {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (!loadMoreBtn) return;

    loadMoreBtn.disabled = true;
    loadMoreBtn.classList.add('loading');
    loadMoreBtn.textContent = 'Loading...';

    try {
        const response = await fetch('/api/load_more_papers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId }),
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
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonString = line.substring(6);
                    const data = JSON.parse(jsonString);

                    if (data.thought) {
                        console.log('Agent thought:', data.thought);
                    } else if (data.recommendations) {
                        data.recommendations.forEach((paper) => {
                            const card = createPaperCard(paper);
                            card.classList.add('new-replacement');
                            setTimeout(() => {
                                card.classList.remove('new-replacement');
                            }, 5000);
                            recommendationsContainer.appendChild(card);
                            window.originalCardOrder.push(card);
                        });

                        window.currentRecommendations = window.currentRecommendations.concat(data.recommendations);
                        window.currentDisplayCount = window.currentRecommendations.length;

                        if (typeof filterAndSortPapers === 'function') {
                            filterAndSortPapers();
                        }
                    } else if (data.error) {
                        console.error('Server-side error:', data.error);
                        if (thoughtsContainer) {
                            thoughtsContainer.innerHTML += `<p>Error loading more papers: ${data.error}</p>`;
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error('Failed to load more papers:', error);
        if (thoughtsContainer) {
            thoughtsContainer.innerHTML += `<p>Failed to load more papers: ${error.message}</p>`;
        }
    } finally {
        loadMoreBtn.disabled = false;
        loadMoreBtn.classList.remove('loading');
        loadMoreBtn.textContent = 'Load More';
    }
}

function showLoadMoreButton() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.style.display = 'block';
    }
}

function setupLoadMoreButton(projectId, recommendationsContainer, thoughtsContainer) {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            loadMorePapers(projectId, recommendationsContainer, thoughtsContainer);
        });
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

        const paperHash = clickedStar.closest('.recommendation-card').dataset.paperHash;
        const currentProjectId = window.location.pathname.split('/').pop();

        // For low ratings, remember the card position for replacement
        let cardToReplace = null;
        let cardIndex = -1;
        if (value <= 2) {
            cardToReplace = clickedStar.closest('.recommendation-card');
            // Only look for cards in the recommendations container, not pubsub papers
            const allCards = Array.from(recommendationsContainer.querySelectorAll('.recommendation-card'));
            cardIndex = allCards.indexOf(cardToReplace);

            // Keep the space occupied but make it invisible
            cardToReplace.style.opacity = '0';
            cardToReplace.style.visibility = 'hidden';
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

        fetch('/api/rate_paper', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_hash: paperHash, rating: value, project_id: currentProjectId })
        })
        .then(res => {
            if (!res.ok) {
                const card = clickedStar.closest('.recommendation-card');
                if (card) {
                    card.dataset.rating = value;
                }
                if (typeof filterAndSortPapers === 'function') {
                    filterAndSortPapers();
                }
                return { status: 'success', message: 'Rating updated locally' };
            }
            return res.json();
        })
        .then(data => {
            if (data.status === 'success') {
                const card = clickedStar.closest('.recommendation-card');
                if (card) {
                    card.dataset.rating = value;
                }

                // Check if a replacement was performed
                if (data.replacement && data.replacement.status === 'success') {
                    const replacementDetails = data.replacement;
                    if (replacementDetails.replacement_title) {
                        showNotification('🔄', 'Paper Replaced!', `Added: "${replacementDetails.replacement_title}"`);
                    }

                    // Insert the replacement paper at the exact same position
                    if (cardIndex >= 0 && replacementDetails.replacement_title) {
                        insertReplacementPaper(replacementDetails, cardIndex, recommendationsContainer);
                    } else {
                        refreshRecommendations(recommendationsContainer, currentProjectId);
                    }
                } else if (value >= 3) {
                    const paperTitle = clickedStar.closest('.recommendation-card').querySelector('h3').textContent;
                    showNotification('⭐', 'Paper Rated Highly!', `The agent will recommend more papers similar to: "${paperTitle}"`);
                }

                        if (typeof filterAndSortPapers === 'function') {
                            filterAndSortPapers();
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

// Function to insert replacement paper at specific position
function insertReplacementPaper(replacementDetails, position, container) {
    // Find the invisible card at the specified position
    const allCards = Array.from(container.querySelectorAll('.recommendation-card'));
    const invisibleCard = allCards[position];

    if (invisibleCard && invisibleCard.style.visibility === 'hidden') {
        const placeholder = container.querySelector('.replacement-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        // Replace the invisible card's content
        invisibleCard.dataset.paperHash = replacementDetails.replacement_paper_hash;
        invisibleCard.dataset.title = replacementDetails.replacement_title.toLowerCase();
        invisibleCard.dataset.rating = '0';
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

        invisibleCard.style.visibility = 'visible';
        invisibleCard.style.opacity = '0';
        invisibleCard.style.transform = 'scale(0.8)';
        invisibleCard.style.position = '';
        invisibleCard.style.zIndex = '';

        setTimeout(() => {
            invisibleCard.style.opacity = '1';
            invisibleCard.style.transform = 'scale(1)';
        }, 100);

        setTimeout(() => {
            invisibleCard.classList.remove('new-replacement');
        }, 3000);
    }
}

// Search Panel Functions
function showSearchPanel() {
    const searchPanel = document.getElementById('searchPanel');
    if (searchPanel) {
        searchPanel.style.display = 'block';
    }
}

function setupSearchPanel() {
    const titleSearchInput = document.getElementById('titleSearchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const sortSelect = document.getElementById('sortSelect');
    const filterSelect = document.getElementById('filterSelect');
    const clearSortBtn = document.getElementById('clearSortBtn');
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    const resultsCount = document.getElementById('resultsCount');

    if (!titleSearchInput || !clearSearchBtn || !sortSelect || !filterSelect || !clearSortBtn || !clearFilterBtn || !resultsCount) {
        return;
    }

    titleSearchInput.addEventListener('input', debounce(() => {
        filterAndSortPapers();
        updateClearButton();
    }, 300));

    clearSearchBtn.addEventListener('click', () => {
        titleSearchInput.value = '';
        filterAndSortPapers();
        updateClearButton();
    });

    clearSortBtn.addEventListener('click', () => {
        sortSelect.value = '';
        filterAndSortPapers();
        updateDropdownButtons();
    });

    clearFilterBtn.addEventListener('click', () => {
        filterSelect.value = '';
        filterAndSortPapers();
        updateDropdownButtons();
    });

    // Show/hide clear search button based on input content
    function updateClearButton() {
        const hasSearchContent = titleSearchInput.value.trim().length > 0;
        if (hasSearchContent) {
            clearSearchBtn.classList.add('visible');
        } else {
            clearSearchBtn.classList.remove('visible');
        }
    }

    // Show/hide clear buttons and dropdown styles based on current selection
    function updateDropdownButtons() {
        const sortDropdown = sortSelect.parentElement;
        const filterDropdown = filterSelect.parentElement;

        const hasSortSelection = sortSelect.value && sortSelect.value !== '' && sortSelect.value !== 'relevance';
        const hasFilterSelection = filterSelect.value && filterSelect.value !== '';

        if (hasSortSelection) {
            sortDropdown.classList.add('has-selection');
            clearSortBtn.classList.add('visible');
        } else {
            sortDropdown.classList.remove('has-selection');
            clearSortBtn.classList.remove('visible');
        }

        if (hasFilterSelection) {
            filterDropdown.classList.add('has-selection');
            clearFilterBtn.classList.add('visible');
        } else {
            filterDropdown.classList.remove('has-selection');
            clearFilterBtn.classList.remove('visible');
        }
    }

    sortSelect.addEventListener('change', () => {
        filterAndSortPapers();
        updateDropdownButtons();
    });

    filterSelect.addEventListener('change', () => {
        filterAndSortPapers();
        updateDropdownButtons();
    });

    updateDropdownButtons();
}

// Filter and sort visible papers based on search input and dropdowns
function filterAndSortPapers() {
    const titleSearchInput = document.getElementById('titleSearchInput');
    const sortSelect = document.getElementById('sortSelect');
    const filterSelect = document.getElementById('filterSelect');
    const resultsCount = document.getElementById('resultsCount');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const recommendationsContainer = document.getElementById('recommendationsContainer');

    // Only count cards in the recommendations container, not pubsub papers
    const cards = recommendationsContainer ? recommendationsContainer.querySelectorAll('.recommendation-card') : [];

    if (!titleSearchInput || !sortSelect || !filterSelect || !resultsCount) return;

    const searchTerm = titleSearchInput.value.toLowerCase().trim();
    const sortBy = sortSelect.value;
    const filterBy = filterSelect.value;

    let visibleCards = 0;

    cards.forEach(card => {
        let shouldShow = true;

        // Filter by title match
        if (searchTerm) {
            const title = card.dataset.title || '';
            if (!title.includes(searchTerm)) {
                shouldShow = false;
            }
        }

        // Filter by rating status (rated or unrated)
        if (shouldShow && filterBy && filterBy !== '') {
            const rating = parseInt(card.dataset.rating) || 0;

            switch (filterBy) {
                case 'rated':
                    if (rating === 0) shouldShow = false;
                    break;
                case 'unrated':
                    if (rating > 0) shouldShow = false;
                    break;
            }
        }

        // Show/hide cards and optionally highlight matches
        if (shouldShow) {
            card.classList.remove('hidden');
            if (searchTerm && card.dataset.title.includes(searchTerm)) {
                card.classList.add('highlighted');
            } else {
                card.classList.remove('highlighted');
            }
            visibleCards++;
        } else {
            card.classList.add('hidden');
            card.classList.remove('highlighted');
        }
    });

    const visibleCardsArray = Array.from(cards).filter(card => !card.classList.contains('hidden'));

    // Handle sorting if a valid option is selected
    if (sortBy && sortBy !== '') {
        if (sortBy === 'relevance') {
            if (recommendationsContainer && window.originalCardOrder) {
                window.originalCardOrder.forEach(card => {
                    if (!card.classList.contains('hidden')) {
                        recommendationsContainer.appendChild(card);
                    }
                });
            }
        } else {
            // Sort visible cards by title or rating
            visibleCardsArray.sort((a, b) => {
                switch (sortBy) {
                    case 'title':
                        const titleA = (a.dataset.title || '').toLowerCase();
                        const titleB = (b.dataset.title || '').toLowerCase();
                        return titleA.localeCompare(titleB);

                    case 'rating':
                        const ratingA = parseInt(a.dataset.rating) || 0;
                        const ratingB = parseInt(b.dataset.rating) || 0;
                        return ratingB - ratingA;

                    case 'date':
                        return 0;

                    default:
                        return 0;
                }
            });

            if (recommendationsContainer) {
                visibleCardsArray.forEach(card => {
                    recommendationsContainer.appendChild(card);
                });
            }
        }
    }

    resultsCount.textContent = `${visibleCards} paper${visibleCards !== 1 ? 's' : ''} found`;

    // Show/hide "Load More" button based on filtering
    if (loadMoreBtn) {
        if (searchTerm || filterBy) {
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.style.display = 'block';
        }
    }
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Function to refresh recommendations (fallback for replacements)
function refreshRecommendations(container, projectId) {
    fetchRecommendationsStream(projectId, document.getElementById('agentThoughtsContainer'), container);
}
