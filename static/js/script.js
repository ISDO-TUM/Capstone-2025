document.addEventListener('DOMContentLoaded', () => {
    const handleRouting = () => {
        const path = window.location.pathname;

        if (path === '/create-project') {
           setupPDFUpload();
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
    const hardcodedProjects = [
        // 30 example projects with name, description, tags, and creation date
        {
            name: "AI for Drug Discovery",
            description: "Leveraging deep learning to accelerate the identification of novel drug candidates for rare diseases.",
            tags: ["AI", "Drug Discovery", "Deep Learning", "Healthcare"],
            date: "2024-01-15"
        },
        {
            name: "Climate Change Impact Analysis",
            description: "Analyzing satellite data to predict the long-term effects of climate change on coastal regions.",
            tags: ["Climate", "Satellite", "Prediction", "Environment"],
            date: "2024-02-02"
        },
        {
            name: "Quantum Computing Algorithms",
            description: "Developing new quantum algorithms for optimization problems in logistics.",
            tags: ["Quantum", "Algorithms", "Optimization", "Logistics"],
            date: "2024-01-28"
        },
        {
            name: "Cancer Genomics",
            description: "Integrating multi-omics data to identify biomarkers for early cancer detection.",
            tags: ["Genomics", "Cancer", "Biomarkers", "Multi-omics"],
            date: "2024-03-10"
        },
        {
            name: "Renewable Energy Forecasting",
            description: "Machine learning models for predicting solar and wind energy production.",
            tags: ["Renewable", "Energy", "Forecasting", "Machine Learning"],
            date: "2024-02-18"
        },
        {
            name: "Social Network Analysis",
            description: "Studying the spread of information and influence in online social networks.",
            tags: ["Social Network", "Influence", "Information Spread", "Data Science"],
            date: "2024-01-22"
        },
        {
            name: "Autonomous Vehicles Safety",
            description: "Evaluating safety protocols and AI decision-making in self-driving cars.",
            tags: ["Autonomous", "Vehicles", "Safety", "AI"],
            date: "2024-03-01"
        },
        {
            name: "Brain-Computer Interfaces",
            description: "Exploring non-invasive methods for direct communication between brain and computer systems.",
            tags: ["Brain", "BCI", "Neuroscience", "Interfaces"],
            date: "2024-02-25"
        },
        {
            name: "Smart Agriculture",
            description: "IoT and AI for precision farming and crop yield optimization.",
            tags: ["Agriculture", "IoT", "AI", "Precision Farming"],
            date: "2024-01-30"
        },
        {
            name: "Natural Language Understanding",
            description: "Advancing NLP models for better comprehension of scientific literature.",
            tags: ["NLP", "Language", "AI", "Literature"],
            date: "2024-02-12"
        },
        {
            name: "Materials Discovery",
            description: "AI-driven search for new materials with unique electronic properties.",
            tags: ["Materials", "AI", "Discovery", "Electronics"],
            date: "2024-03-05"
        },
        {
            name: "Urban Mobility Planning",
            description: "Simulation and optimization of public transport systems in megacities.",
            tags: ["Urban", "Mobility", "Transport", "Simulation"],
            date: "2024-01-18"
        },
        {
            name: "Protein Structure Prediction",
            description: "Deep learning for accurate prediction of protein folding and structure.",
            tags: ["Protein", "Structure", "Deep Learning", "Biology"],
            date: "2024-02-20"
        },
        {
            name: "Digital Humanities",
            description: "Text mining and visualization for historical document analysis.",
            tags: ["Humanities", "Text Mining", "Visualization", "History"],
            date: "2024-03-08"
        },
        {
            name: "Robotics in Surgery",
            description: "Evaluating the precision and outcomes of robot-assisted surgical procedures.",
            tags: ["Robotics", "Surgery", "Precision", "Healthcare"],
            date: "2024-01-25"
        },
        {
            name: "Wildlife Conservation AI",
            description: "Using AI to monitor endangered species and prevent poaching.",
            tags: ["Wildlife", "Conservation", "AI", "Monitoring"],
            date: "2024-02-28"
        },
        {
            name: "Blockchain for Science",
            description: "Decentralized data sharing and reproducibility in scientific research.",
            tags: ["Blockchain", "Reproducibility", "Data Sharing", "Science"],
            date: "2024-03-12"
        },
        {
            name: "Personalized Medicine",
            description: "Genetic and lifestyle data for tailored healthcare solutions.",
            tags: ["Personalized", "Medicine", "Genetics", "Healthcare"],
            date: "2024-01-27"
        },
        {
            name: "Astrophysics Simulations",
            description: "High-performance computing for simulating galaxy formation.",
            tags: ["Astrophysics", "Simulation", "Galaxy", "HPC"],
            date: "2024-02-15"
        },
        {
            name: "Emotion Recognition",
            description: "AI models for detecting emotions in speech and facial expressions.",
            tags: ["Emotion", "Recognition", "AI", "Speech"],
            date: "2024-03-03"
        },
        {
            name: "Smart Grids",
            description: "Optimizing energy distribution using real-time data and AI.",
            tags: ["Smart Grid", "Energy", "AI", "Optimization"],
            date: "2024-01-19"
        },
        {
            name: "Microbiome Analysis",
            description: "Studying the human microbiome's role in health and disease.",
            tags: ["Microbiome", "Health", "Disease", "Biology"],
            date: "2024-02-22"
        },
        {
            name: "Edge Computing for IoT",
            description: "Low-latency data processing at the edge for IoT devices.",
            tags: ["Edge", "IoT", "Computing", "Data"],
            date: "2024-03-07"
        },
        {
            name: "Virtual Reality in Education",
            description: "Immersive VR experiences for interactive science learning.",
            tags: ["VR", "Education", "Immersive", "Science"],
            date: "2024-01-23"
        },
        {
            name: "Gene Editing Ethics",
            description: "Exploring the ethical implications of CRISPR and gene editing.",
            tags: ["Gene Editing", "Ethics", "CRISPR", "Biotech"],
            date: "2024-02-27"
        },
        {
            name: "Financial Market Prediction",
            description: "AI and statistical models for stock and crypto market forecasting.",
            tags: ["Finance", "Prediction", "AI", "Markets"],
            date: "2024-03-11"
        },
        {
            name: "Speech Synthesis",
            description: "Neural networks for natural-sounding text-to-speech systems.",
            tags: ["Speech", "Synthesis", "Neural Networks", "Audio"],
            date: "2024-01-29"
        },
        {
            name: "Food Security Monitoring",
            description: "Remote sensing and AI for global food supply chain monitoring.",
            tags: ["Food", "Security", "Remote Sensing", "AI"],
            date: "2024-02-24"
        },
        {
            name: "Exoplanet Detection",
            description: "Machine learning for identifying exoplanets in telescope data.",
            tags: ["Exoplanet", "Detection", "Machine Learning", "Astronomy"],
            date: "2024-03-09"
        },
        {
            name: "Digital Twin Manufacturing",
            description: "Simulating and optimizing manufacturing processes with digital twins.",
            tags: ["Digital Twin", "Manufacturing", "Simulation", "Optimization"],
            date: "2024-01-31"
        },
        {
            name: "Mental Health Chatbots",
            description: "Conversational AI for mental health support and early intervention.",
            tags: ["Mental Health", "Chatbot", "AI", "Support"],
            date: "2024-02-26"
        }
    ];

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
                <div class="project-title">${project.name}</div>
                <div class="project-description">${truncatedDescription}</div>
                <div class="project-tags">
                    ${project.tags.map(tag => `<span class="project-tag">${tag}</span>`).join(' ')}
                </div>
                <div class="project-date">Created: ${project.date}</div>
            `;
            // Optionally, add click event for future navigation or toast
            card.addEventListener('click', () => {
                // For now, just a simple animation or toast
                card.classList.add('card-clicked');
                setTimeout(() => card.classList.remove('card-clicked'), 400);
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
        renderProjects(hardcodedProjects);
        const searchInput = document.getElementById('projectSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const filtered = filterProjectsBySearch(hardcodedProjects, e.target.value);
                renderProjects(filtered);
            });
        }
        // Animate cards on scroll (again, in case of resize/search)
        window.addEventListener('resize', animateCardsOnScroll);
        window.addEventListener('scroll', animateCardsOnScroll);
    }

    handleRouting();
});