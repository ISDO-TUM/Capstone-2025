    // Dummy papers for testing PubSub (take this out and then fetch to backend)
const dummyPubSubPapers = [
    {
      title: "A Survey on LLM Agents",
      description: "This paper reviews advances in large language model agents. It summarizes use cases and open challenges.",
      link: "https://arxiv.org/abs/2401.00001"
    },
    {
      title: "Generative AI for Science",
      description: "Overview of how generative AI is changing the scientific process. Two key examples included.",
      link: "https://arxiv.org/abs/2401.00002"
    },
    {
      title: "Reinforcement Learning with LLMs",
      description: "Examines how large language models can be fine-tuned with reinforcement learning techniques for improved task performance.",
      link: "https://arxiv.org/abs/2401.00003"
    },
    {
      title: "Ethics in Generative AI",
      description: "Analyzes ethical considerations in deploying generative AI systems, including bias mitigation and transparency.",
      link: "https://arxiv.org/abs/2401.00004"
    },
    {
      title: "Multi-Agent Collaboration with LLMs",
      description: "Studies architectures where multiple LLM-based agents interact to solve complex, multi-step problems collaboratively.",
      link: "https://arxiv.org/abs/2401.00005"
    }
  ];


// 1) Always render PubSub bar // This is called from loadProjectOverviewData()
function renderPubSubSection() {
    const container = document.getElementById('pubsubPapersContainer');
    renderPubSubPapers(dummyPubSubPapers, container);
  }
  
  // 2) newsletter form always ready
  function setupPubSubForm() {
    const form = document.getElementById('pubsubSubscribeForm');
    const emailInput = document.getElementById('pubsubEmail');
  
    form.addEventListener('submit', event => {
      event.preventDefault();
      const email = emailInput.value.trim();
      if (!email) return;
  
      fetch('/api/pubsub-subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })
      .then(res => {
        if (res.ok) {
          alert('Thanks for subscribing!');
          emailInput.value = '';
        } else {
          alert('Subscription failed. Please try again.');
        }
      })
      .catch(() => {
        alert('Network error. Please try later.');
      });
    });
  }
  
  function renderPubSubPapers(papers, container) {
    container.innerHTML = '';
    papers.forEach(paper => {
      const card = document.createElement('div');
      card.classList.add('recommendation-card'); // Use sae style
      card.style.minWidth = '240px';
  
      const titleEl = document.createElement('h4');
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
        const agentThoughtsContainer = document.getElementById('agentThoughtsContainer');

        if (titleDisplay) titleDisplay.textContent = projectData.title;
        if (descriptionDisplay) descriptionDisplay.textContent = projectData.description;
        if (document.title && titleDisplay) document.title = `Project: ${projectData.title}`;
        
        renderPubSubSection(); //calling PubSub

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

    handleRouting();
});

