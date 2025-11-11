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

//loadPubSubPapers loads the latest papers after recommendations are loaded
async function loadPubSubPapers(projectId) {
    const container = document.getElementById('pubsubPapersContainer');
    if (!container) return;

    try {
        // First update the newsletter papers
        const updateRes = await fetch('/api/pubsub/update_newsletter_papers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ projectId }),
            credentials: 'include'
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

        // Then fetch the papers
        const papers = await fetch(
            `/api/pubsub/get_newsletter_papers?projectId=${projectId}`, {
                credentials: 'include'
            }
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
            // Keep the loading placeholder if no papers are available
            console.log('📭 No papers available yet');
        } else {
            console.log('📬 Rendering real PubSub papers:', papers);
            renderPubSubPapers(papers, container);
        }
    } catch (err) {
        console.error('Error loading PubSub papers:', err);
    }
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
        const logHistory  = document.getElementById('logHistory').value;

            // POST to real endpoint instead of localStorage
            const res = await fetch('/api/projects', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ title, description, logHistory })
              credentials: 'include'
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

        // Show loading placeholder immediately
        container.innerHTML = '<p class="no-papers-placeholder">⌛ Latest papers will appear here soon...</p>';

        const params= new URLSearchParams(window.location.search);
        const updateRecommendations = params.get('updateRecommendations') === 'true';
        loadProjectOverviewData(projectId, project.description, updateRecommendations);
        if (updateRecommendations) {
            history.replaceState({}, '', window.location.pathname);
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
                body: formData,
                credentials: 'include'
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

        // Track the last thought element for subunit rendering
        let lastThoughtEl = null;

        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectId: projectId,
                    update_recommendations : updateRecommendations //set this to true only if new project or if future 'refresh recommendations' button pressed
                }),
                credentials: 'include'
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
                    console.info("Received agent message")
                    console.info(data)
                    if (data.thought) {
                        const thoughtEl = document.createElement('li');

                    let content = data.thought;
                    let icon = '🧠';
                    if (content.startsWith('Calling tool:')) {
                        icon = '🛠️';
                        content = content.replace('Calling tool:', '<strong>Calling tool:</strong>');
                    } else if (content.startsWith('Tool response received:')) {
                        icon = '✅';
                        content = content.replace('Tool response received:', '<strong>Tool response received:</strong>');
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

    // Title row with key metrics on the right
    const titleRow = document.createElement('div');
    titleRow.style.cssText = 'display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 12px;';

    const titleEl = document.createElement('h3');
    titleEl.textContent = paper.title;
    titleEl.style.cssText = 'margin: 0; flex: 1;';

    // Key metrics on the right side of title
    const keyMetrics = document.createElement('div');
    keyMetrics.style.cssText = 'display: flex; gap: 16px; align-items: center; flex-shrink: 0;';

    let metricsHTML = '';

    // FWCI with tooltip and smart formatting
    if (paper.fwci !== undefined && paper.fwci !== null) {
        // Smart formatting: show decimals for values < 10, round for larger values
        const fwciValue = paper.fwci < 10 ? paper.fwci.toFixed(2) : Math.round(paper.fwci);
        const fwciColor = paper.fwci >= 1.5 ? '#28a745' : paper.fwci >= 1.0 ? '#ffc107' : '#6c757d';
        metricsHTML += `
            <div style="text-align: center; position: relative; cursor: help;" class="metric-with-tooltip">
                <div style="color: #6c757d; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">FWCI</div>
                <div style="color: ${fwciColor}; font-size: 18px; font-weight: 700;">${fwciValue}</div>
                <span class="metric-tooltip">Source: OpenAlex API<br>Field-Weighted Citation Impact</span>
            </div>
        `;
    }

    // Citations
    if (paper.cited_by_count !== undefined && paper.cited_by_count !== null) {
        metricsHTML += `
            <div style="text-align: center; position: relative; cursor: help;" class="metric-with-tooltip">
                <div style="color: #6c757d; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Citations</div>
                <div style="color: #212529; font-size: 18px; font-weight: 700;">${paper.cited_by_count}</div>
                <span class="metric-tooltip">Source: OpenAlex API</span>
            </div>
        `;
    }

    // Percentile with badge
    if (paper.citation_normalized_percentile !== undefined && paper.citation_normalized_percentile !== null) {
        const pct = paper.citation_normalized_percentile;
        if (typeof pct === 'object' && pct.value !== undefined) {
            const percentileValue = (pct.value * 100).toFixed(0);
            let badgeColor = '#6c757d';
            let badgeText = '';
            if (pct.is_in_top_1_percent) {
                badgeColor = '#dc3545';
                badgeText = 'TOP 1%';
            } else if (pct.is_in_top_10_percent) {
                badgeColor = '#ffc107';
                badgeText = 'TOP 10%';
            }

            if (badgeText) {
                metricsHTML += `
                    <div style="text-align: center;">
                        <div style="background: ${badgeColor}; color: ${badgeColor === '#ffc107' ? '#212529' : 'white'}; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; white-space: nowrap;">${badgeText}</div>
                        <div style="color: #6c757d; font-size: 11px; margin-top: 2px;">${percentileValue}th</div>
                    </div>
                `;
            } else {
                metricsHTML += `
                    <div style="text-align: center;">
                        <div style="color: #6c757d; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Percentile</div>
                        <div style="color: #212529; font-size: 18px; font-weight: 700;">${percentileValue}%</div>
                    </div>
                `;
            }
        }
    }

    if (metricsHTML) {
        keyMetrics.innerHTML = metricsHTML;
    }

    // Add star rating to the right side
    const topStarRatingEl = document.createElement('div');
    topStarRatingEl.classList.add('star-rating');
    topStarRatingEl.style.cssText = 'display: flex; gap: 4px; padding-left: 16px; border-left: 2px solid #dee2e6;';
    topStarRatingEl.innerHTML = createStarRatingHTML();

    titleRow.appendChild(titleEl);
    if (metricsHTML) {
        titleRow.appendChild(keyMetrics);
    }
    titleRow.appendChild(topStarRatingEl);

    const descriptionEl = document.createElement('p');
    descriptionEl.textContent = paper.description;

    // Authors with icon
    const authorsEl = document.createElement('p');
    authorsEl.style.cssText = 'margin: 8px 0; font-size: 14px; color: #555; display: flex; align-items: center; gap: 8px;';
    if (paper.authors) {
        authorsEl.innerHTML = `<span style="font-size: 16px;">👥</span><span><strong>Authors:</strong> ${paper.authors}</span>`;
    }

    // Year with icon
    const yearEl = document.createElement('p');
    yearEl.style.cssText = 'margin: 8px 0; font-size: 14px; color: #555; display: flex; align-items: center; gap: 8px;';
    if (paper.publication_date) {
        const year = new Date(paper.publication_date).getFullYear();
        yearEl.innerHTML = `<span style="font-size: 16px;">📅</span><span><strong>Year:</strong> ${year}</span>`;
    }

    // Venue with icon
    const venueEl = document.createElement('p');
    venueEl.style.cssText = 'margin: 8px 0; font-size: 14px; color: #555; display: flex; align-items: center; gap: 8px;';
    if (paper.venue_name) {
        let venueText = `<strong>Venue:</strong> ${paper.venue_name}`;
        if (paper.venue_type) {
            venueText += ` <span style="color: #888; font-size: 13px;">(${paper.venue_type})</span>`;
        }
        venueEl.innerHTML = `<span style="font-size: 16px;">🏛️</span><span>${venueText}</span>`;
    }

    // Open Access and PDF with icons
    const accessEl = document.createElement('p');
    accessEl.style.cssText = 'margin: 8px 0; font-size: 14px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;';
    let accessHTML = '';

    // Read Paper button (OpenAlex landing page)
    if (paper.link) {
        accessHTML += `<span style="display: inline-flex; align-items: center; gap: 6px; background: #6c757d; color: white; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: 600; transition: background 0.2s; cursor: pointer;" onmouseover="this.style.background='#5a6268'" onmouseout="this.style.background='#6c757d'" onclick="window.open('${paper.link}', '_blank')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>Read Paper</span>`;
    }

    if (paper.is_oa !== undefined) {
        const oaBadgeColor = paper.is_oa ? '#28a745' : '#6c757d';
        const oaIcon = paper.is_oa ? '🔓' : '🔒';
        const oaText = paper.is_oa ? `Open Access (${paper.oa_status || 'available'})` : 'Closed Access';
        accessHTML += `<span style="display: inline-flex; align-items: center; background: ${oaBadgeColor}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px;">${oaIcon} ${oaText}</span>`;
    }

    // Single PDF button - prioritize pdf_url, fallback to oa_url
    const pdfUrl = paper.pdf_url || (paper.is_oa && paper.oa_url ? paper.oa_url : null);
    if (pdfUrl) {
        accessHTML += `<span style="display: inline-flex; align-items: center; gap: 6px; background: #007bff; color: white; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: 600; transition: background 0.2s; cursor: pointer;" onmouseover="this.style.background='#0056b3'" onmouseout="this.style.background='#007bff'" onclick="window.open('${pdfUrl}', '_blank')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>PDF</span>`;
    }
    if (accessHTML) accessEl.innerHTML = accessHTML;

    card.dataset.paperHash = paper.hash;
    card.dataset.title = paper.title.toLowerCase();
    card.dataset.rating = paper.rating || 0;
    card.dataset.year = paper.publication_date ? new Date(paper.publication_date).getFullYear() : 0;
    card.dataset.citations = paper.cited_by_count || 0;
    card.dataset.fwci = paper.fwci || 0;
    card.dataset.percentile = (paper.citation_normalized_percentile && typeof paper.citation_normalized_percentile === 'object') ? (paper.citation_normalized_percentile.value || 0) : (paper.citation_normalized_percentile || 0);
    card.dataset.venue = paper.venue_name ? paper.venue_name.toLowerCase() : '';
    card.dataset.isOa = paper.is_oa ? '1' : '0';

    card.appendChild(titleRow);
    card.appendChild(descriptionEl);
    if (paper.authors) card.appendChild(authorsEl);
    if (paper.publication_date) card.appendChild(yearEl);
    if (paper.venue_name) card.appendChild(venueEl);
    if (accessEl.innerHTML) card.appendChild(accessEl);

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

    // Load PubSub papers after recommendations are rendered
    const projectId = window.location.pathname.split('/').pop();
    if (projectId) {
        loadPubSubPapers(projectId);
    }
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

            // Update the top input field to reflect the new query
            const topInput = document.querySelector('input#projectTitle, textarea#projectDescription, input[type="text"], textarea');
            if (topInput) {
                topInput.value = newQuery;
            }

            // Get projectId and other context
            const projectId = window.location.pathname.split('/').pop();
            const recommendationsContainer = document.getElementById('recommendationsContainer');
            const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');

            // Clear previous thoughts and recommendations
            agentThoughtsContainer.innerHTML = '<p>🧠 Agent is thinking...</p>';
            recommendationsContainer.innerHTML = '<p>⌛ Waiting for agent to provide recommendations...</p>';

            // Update project prompt in backend, then update UI and start new recommendation stream
            updateProjectPrompt(projectId, newQuery)
                .then(data => {
                    // Update the description in the UI
                    const descDisplay = document.getElementById('projectDescriptionDisplay');
                    if (descDisplay && data.description) {
                        descDisplay.textContent = data.description;
                    }
                    // Now start the new recommendation stream
                    return fetchRecommendationsStream(projectId, newQuery, agentThoughtsContainer, recommendationsContainer, true);
                })
                .catch(error => {
                    console.error("Error updating project prompt or fetching recommendations:", error);
                    agentThoughtsContainer.innerHTML += '<p>❌ Error processing new query.</p>';
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

            // Update the top input field to reflect the new query
            const topInput = document.querySelector('input#projectTitle, textarea#projectDescription, input[type="text"], textarea');
            if (topInput) {
                topInput.value = newQuery;
            }

            // Get projectId and other context
            const projectId = window.location.pathname.split('/').pop();
            const recommendationsContainer = document.getElementById('recommendationsContainer');
            const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');

            // Clear previous thoughts and recommendations
            agentThoughtsContainer.innerHTML = '<p>🧠 Agent is thinking...</p>';
            recommendationsContainer.innerHTML = '<p>⌛ Waiting for agent to provide recommendations...</p>';

            // Update project prompt in backend, then update UI and start new recommendation stream
            updateProjectPrompt(projectId, newQuery)
                .then(data => {
                    // Update the description in the UI
                    const descDisplay = document.getElementById('projectDescriptionDisplay');
                    if (descDisplay && data.description) {
                        descDisplay.textContent = data.description;
                    }
                    // Now start the new recommendation stream
                    return fetchRecommendationsStream(projectId, newQuery, agentThoughtsContainer, recommendationsContainer, true);
                })
                .catch(error => {
                    console.error("Error updating project prompt or fetching recommendations:", error);
                    agentThoughtsContainer.innerHTML += '<p>❌ Error processing new query.</p>';
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
    const fadeOverlay = document.getElementById('descriptionFadeOverlay');
    const oldControls = document.getElementById('descriptionControls');
    if (oldControls && oldControls.parentNode) oldControls.parentNode.removeChild(oldControls);

    if (!descriptionDisplay || !descriptionWrapper || !fadeOverlay) return;

    const wordCount = description.trim().split(/\s+/).length;

    if (wordCount > 500) {
        // Create controls and toggle button dynamically
        const controls = document.createElement('div');
        controls.className = 'description-controls';
        controls.id = 'descriptionControls';
        const toggleButton = document.createElement('button');
        toggleButton.className = 'expand-btn';
        toggleButton.id = 'descriptionToggle';
        toggleButton.innerHTML = `
            <span class="expand-text">Show full description</span>
            <svg class="expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <polyline points="6,9 12,15 18,9"></polyline>
            </svg>
        `;
        controls.appendChild(toggleButton);
        descriptionWrapper.appendChild(controls);
        const expandText = toggleButton.querySelector('.expand-text');

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

    function renderProjects(projects, isSearchResult = false) {
        const projectsList = document.getElementById('projectsList');
        const noProjectsContainer = document.getElementById('noProjectsContainer');
        const searchBarWrapper = document.querySelector('.search-bar-wrapper');

        if (!projectsList) return;

        // Check if there are no projects (only show no projects screen if it's not a search result)
        if ((!projects || projects.length === 0) && !isSearchResult) {
            // Hide search bar and projects list, show no projects message
            if (searchBarWrapper) {
                searchBarWrapper.classList.add('hidden');
                searchBarWrapper.style.display = 'none';
            }
            if (projectsList) projectsList.style.display = 'none';
            if (noProjectsContainer) {
                noProjectsContainer.style.display = 'flex';
            }
            return;
        }

        // Show search bar and projects list, hide no projects message
        if (searchBarWrapper) {
            searchBarWrapper.classList.remove('hidden');
            searchBarWrapper.style.display = 'flex';
        }
        if (projectsList) projectsList.style.display = 'grid';
        if (noProjectsContainer) noProjectsContainer.style.display = 'none';

        projectsList.innerHTML = '';

        // If no search results, show empty state but keep search bar visible
        if (!projects || projects.length === 0) {
            projectsList.innerHTML = '<div style="text-align: center; color: #6c757d; padding: 40px; font-size: 1.1rem;">No projects found matching your search.</div>';
            return;
        }

        // Sort projects by date descending (latest first)
        projects = projects.slice().sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateB - dateA;
        });
        projects.forEach((project, idx) => {
            const card = document.createElement('div');
            card.className = 'project-card';
            card.style.animationDelay = `${idx * 0.04 + 0.1}s`;
            // Truncate description to 120 chars for safety
            const truncatedDescription = truncateText(project.description, 120);
            // Format date to human-readable string, add 2 hours for CET
            let formattedDate = project.date;
            if (project.date) {
                const d = new Date(project.date);
                if (!isNaN(d)) {
                    d.setHours(d.getHours() + 2); // Add 2 hours for CET
                    formattedDate = d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                }
            }
            card.innerHTML = `
                <div class="project-card-header">
                    <div class="project-title">${project.title}</div>
                    <button class="delete-project-btn" data-project-id="${project.project_id}" title="Delete project" aria-label="Delete project">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                    </button>
                </div>
                <div class="project-description">${truncatedDescription}</div>
                <div class="project-tags">
                    ${project.tags.map(tag => `<span class="project-tag">${tag}</span>`).join(' ')}
                </div>
                <div class="project-date">Created: ${formattedDate}</div>
            `;
            
            // Add delete button handler
            const deleteBtn = card.querySelector('.delete-project-btn');
            deleteBtn.addEventListener('click', async (e) => {
                e.stopPropagation(); // Prevent card click navigation
                
                if (confirm(`Are you sure you want to delete "${project.title}"? This action cannot be undone.`)) {
                    try {
                        const response = await fetch(`/api/project/${project.project_id}`, {
                            method: 'DELETE',
                            credentials: 'include'
                        });
                        
                        if (response.ok) {
                            // Remove card with animation
                            card.style.opacity = '0';
                            card.style.transform = 'scale(0.8)';
                            setTimeout(() => {
                                card.remove();
                                // Reload projects to update the list
                                loadProjectsFromAPI();
                            }, 300);
                        } else {
                            const data = await response.json();
                            alert(`Failed to delete project: ${data.error || 'Unknown error'}`);
                        }
                    } catch (error) {
                        console.error('Error deleting project:', error);
                        alert('Failed to delete project. Please try again.');
                    }
                }
            });
            
            // Navigate to project page on card click
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
            renderProjects(allProjects, false); // Not a search result
        });

        const searchInput = document.getElementById('projectSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const filtered = filterProjectsBySearch(allProjects, e.target.value);
                renderProjects(filtered, true); // Mark as search result
            });
        }
        // Animate cards on scroll (again, in case of resize/search)
        window.addEventListener('resize', animateCardsOnScroll);
        window.addEventListener('scroll', animateCardsOnScroll);
    }

    if (window.location.pathname.startsWith('/project/')) {
        const params = new URLSearchParams(window.location.search);
        const isNewProject = params.get('updateRecommendations') === 'true';
        if (!isNewProject) {
            const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');
            if (agentThoughtsContainer) {
                agentThoughtsContainer.innerHTML = '';
                const section = document.querySelector('.agent-thoughts-section');
                if (section) section.style.display = 'none';
            }
        }
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
            body: JSON.stringify({ paper_hash: paperHash, rating: value, project_id: currentProjectId }),
            credentials: 'include'
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
    const sortInfoIcon = document.getElementById('sortInfoIcon');

    if (!titleSearchInput || !clearSearchBtn || !sortSelect || !filterSelect || !clearSortBtn || !clearFilterBtn || !resultsCount) {
        return;
    }

    // Tooltip messages for each sort option
    const sortTooltips = {
        '': '🎯 Default Sorting: Papers are ranked by relevance to your project using AI similarity matching',
        'relevance': '🎯 Default Sorting: Papers are ranked by relevance to your project using AI similarity matching',
        'title': 'Papers are sorted alphabetically by title',
        'rating': 'Papers are sorted by your ratings, highest first',
        'year': 'Papers are sorted by publication year, newest first',
        'citations': 'Papers are sorted by citation count, most cited first',
        'fwci': 'Papers are sorted by Field-Weighted Citation Impact, highest first',
        'percentile': 'Papers are sorted by citation percentile, highest first',
        'oa': 'Open Access papers are shown first'
    };

    // Function to update tooltip based on current sort selection
    function updateSortTooltip() {
        if (sortInfoIcon) {
            const currentSort = sortSelect.value || '';
            const tooltipText = sortTooltips[currentSort] || sortTooltips[''];
            
            // Remove any existing tooltip
            const existingTooltip = sortInfoIcon.querySelector('.sort-tooltip-popup');
            if (existingTooltip) {
                existingTooltip.remove();
            }
            
            // Create new tooltip popup
            const tooltip = document.createElement('div');
            tooltip.className = 'sort-tooltip-popup';
            tooltip.textContent = tooltipText;
            sortInfoIcon.appendChild(tooltip);
        }
    }

    // Initialize tooltip
    updateSortTooltip();

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
        updateSortTooltip();
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
        updateSortTooltip();
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

        // Filter by rating status or OA status
        if (shouldShow && filterBy && filterBy !== '') {
            const rating = parseInt(card.dataset.rating) || 0;
            const isOa = parseInt(card.dataset.isOa) || 0;

            switch (filterBy) {
                case 'rated':
                    if (rating === 0) shouldShow = false;
                    break;
                case 'unrated':
                    if (rating > 0) shouldShow = false;
                    break;
                case 'open-access':
                    if (isOa === 0) shouldShow = false;
                    break;
                case 'closed-access':
                    if (isOa === 1) shouldShow = false;
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
            // Sort visible cards by selected criterion
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

                    case 'year':
                        const yearA = parseInt(a.dataset.year) || 0;
                        const yearB = parseInt(b.dataset.year) || 0;
                        return yearB - yearA; // Newest first

                    case 'citations':
                        const citationsA = parseInt(a.dataset.citations) || 0;
                        const citationsB = parseInt(b.dataset.citations) || 0;
                        return citationsB - citationsA; // Most first

                    case 'fwci':
                        const fwciA = parseFloat(a.dataset.fwci) || 0;
                        const fwciB = parseFloat(b.dataset.fwci) || 0;
                        return fwciB - fwciA; // Highest first

                    case 'percentile':
                        const percentileA = parseFloat(a.dataset.percentile) || 0;
                        const percentileB = parseFloat(b.dataset.percentile) || 0;
                        return percentileB - percentileA; // Highest first

                    case 'oa':
                        const oaA = parseInt(a.dataset.isOa) || 0;
                        const oaB = parseInt(b.dataset.isOa) || 0;
                        return oaB - oaA; // OA first (1 before 0)

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

// Utility to update project prompt in backend and UI
function updateProjectPrompt(projectId, newPrompt) {
    return fetch(`/api/project/${projectId}/update_prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: newPrompt }),
        credentials: 'include'
    })
    .then(response => response.json());
}
