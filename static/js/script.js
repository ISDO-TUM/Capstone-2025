// ←← MOCK DATA PARA DEMO PUBSUB
const dummyPubSubPapers = [
    {
        title: "Learner Motivation and Language Attitudes: A Meta-Analysis",
        description: "A review of studies exploring the relationship between student motivation and their attitudes toward learning English in EFL contexts worldwide.",
        link: "https://arxiv.org/abs/2101.06547"
    },
    {
        title: "Classroom Environment and English Language Learning Attitudes",
        description: "Examines how the physical and social design of the classroom influences students’ attitudes toward English as a foreign language in secondary schools across Asia and Europe.",
        link: "https://arxiv.org/abs/2009.05235"
    },
    {
        title: "Peer Influence on EFL Learner Attitudes: A Longitudinal Study",
        description: "A longitudinal study analyzing how peer interactions affect students’ perceptions and interest in learning English at Latin American high schools.",
        link: "https://arxiv.org/abs/1905.12345"
    },
    {
        title: "Impact of Teaching Materials on EFL Student Motivation",
        description: "Investigates the effect of different types of teaching materials (videos, authentic texts, interactive activities) on the motivation and attitude of EFL students in European institutes.",
        link: "https://arxiv.org/abs/2203.08765"
    },
    {
        title: "Technology Integration and EFL Learner Engagement",
        description: "Analyzes how technological tools (online platforms, mobile apps) enhance students’ attitudes and engagement with English as a foreign language in secondary education settings.",
        link: "https://arxiv.org/abs/2304.01234"
    }
];

  

// ←← PUBSUB UI HELPERS: Definitions first ←←
function renderPubSubSection() {
    document.getElementById('pubsubPapersContainer').innerHTML = '';
}
  
function setupPubSubForm() {
    const form = document.getElementById('pubsubSubscribeForm');
    if (!form) return;        // if there is no #pubsubSubscribeForm, exit
    const emailInput = document.getElementById('pubsubEmail');
    form.addEventListener('submit', e => {
      e.preventDefault();
      alert(`Thanks for subscribing, ${emailInput.value}!`);
      emailInput.value = '';
    });
}
  
function renderPubSubPapers(papers, container) {
    container.innerHTML = '';
    papers.forEach(paper => {
      // 1) crear el div de la card
      const card = document.createElement('div');
      card.classList.add('recommendation-card');
  
      // 2) crear y llenar el h4 del título
      const titleEl = document.createElement('h4');
      titleEl.textContent = paper.title;
  
      // 3) crear el enlace
      const linkEl = document.createElement('a');
      linkEl.href = paper.link;
      linkEl.textContent = "Read Paper";
      linkEl.target = "_blank";
  
      // 4) crear el párrafo de descripción
      const descriptionEl = document.createElement('p');
      descriptionEl.textContent = paper.description;
  
      // 5) ensamblar todo en la card
      card.appendChild(titleEl);
      card.appendChild(linkEl);
      card.appendChild(descriptionEl);
      container.appendChild(card);
    });
}

function setupPDFUpload() {
}

//document.addEventListener('DOMContentLoaded', () => {
    //Invoke form only one time
    //setupPubSubForm();
    // 1) Use async to use await inside
    async function handleRouting () {
        const path = window.location.pathname;

        if (path === '/create-project') {
           setupPDFUpload();
        } else if (path.startsWith('/project/')) {
            const projectId = path.split('/').pop();

            // ——— DEMO MOCK: show dummyPubSubPapers always ———
            const container = document.getElementById('pubsubPapersContainer');
            renderPubSubSection();               // 
            renderPubSubPapers(dummyPubSubPapers, container);
            setupPubSubForm();                   //

            //const projectRes = await fetch(`/api/project/${projectId}`);
            //if (projectRes.ok) {
            //  const projectData = await projectRes.json();
            //  console.log('Project data:', projectData);
            
            //} else {
            //    console.error('Couldnt load project data');
            //}

            // ‹‹ PUBSUB – STEP 1: update backend 
            //await fetch('/api/pubsub/update_newsletter_papers', {
            //    method: 'POST',
            //    headers: { 'Content-Type': 'application/json' },
            //    body: JSON.stringify({ projectId })
            //})
            // ‹‹ PUBSUB – STEP 2: load and render real papers 
            //const container = document.getElementById('pubsubPapersContainer');
            //renderPubSubSection();    // clean or show placeholder
            //const papers = await fetch(`/api/pubsub/get_newsletter_papers?projectId=${projectId}`)
                                    //.then(r => r.json());
            //renderPubSubPapers(papers, container);
            
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
        const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');

        if (titleDisplay) titleDisplay.textContent = projectData.title;
        if (descriptionDisplay) {
            descriptionDisplay.textContent = projectData.description;
            setupCollapsibleDescription(projectData.description);
        }
        if (document.title && titleDisplay) document.title = `Project: ${projectData.title}`;

        if (recommendationsContainer && agentThoughtsContainer) {
            // Set initial state messages
            agentThoughtsContainer.innerHTML = '<p>🧠 Agent is thinking...</p>';
            recommendationsContainer.innerHTML = '<p>⌛ Waiting for agent to provide recommendations...</p>';

            fetchRecommendationsStream(projectData.description, agentThoughtsContainer, recommendationsContainer)
                .catch(error => {
                    console.error("Error fetching recommendations stream:", error);
                    agentThoughtsContainer.innerHTML += '<p>❌ Error communicating with the agent.</p>';
                    recommendationsContainer.innerHTML = '<p>Could not load recommendations at this time.</p>';
                });
        }
    };

    async function fetchRecommendationsStream(projectDescription, thoughtsContainer, recommendationsContainer) {
        console.log(`Starting to stream recommendations based on project description...`);
        thoughtsContainer.innerHTML = ''; // Clear for new thoughts

        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ projectDescription }),
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

            expandText.textContent = isCollapsed ? 'Show full description' : 'Show less';

            toggleButton.addEventListener('click', () => {
                const currentlyCollapsed = descriptionDisplay.classList.contains('collapsed');

                descriptionDisplay.classList.toggle('collapsed', !currentlyCollapsed);
                descriptionDisplay.classList.toggle('expanded', currentlyCollapsed);
                toggleButton.classList.toggle('expanded', currentlyCollapsed);
                fadeOverlay.classList.toggle('visible', !currentlyCollapsed);

                expandText.textContent = !currentlyCollapsed ? 'Show full description' : 'Show less';
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
    handleRouting();
});
