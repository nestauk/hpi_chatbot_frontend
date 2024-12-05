# HPI Chatbot Frontend

The **HPI Chatbot Frontend** is a user-friendly interface for interacting with the [Heat Pump Installer Chatbot](https://github.com/nestauk/-asf_HP_installer_chatbot), built using **Streamlit** and containerised with **Docker** for seamless deployment and scalability.

---

## 🚀 Features

- **Streamlit-based Frontend**: Leverages Streamlit for an interactive and intuitive chatbot experience.
- **Dockerized Deployment**: Simplifies environment setup and ensures consistency across different platforms.
- **Customisable**: Easily configurable to integrate with various chatbot backends.
- **Lightweight & Portable**: Run anywhere Docker is supported.

---

## 🛠️ Getting Started

### Prerequisites

Ensure you have the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## 🔧 Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root based on the `.env.template` file.

---

## ▶️ Running the Application

### Using Docker Compose

To start the application using Docker Compose:

1. Build and run the Docker container:
   ```bash
   docker-compose up --build
   ```
2. Access the application in your browser at: http://localhost:8501


### Standalone Docker Command

To run the app without Docker Compose:

1. Build the Docker image:
```docker build -t hpi-chatbot-frontend .```
2. Run the container:
```docker run -p 8501:8501 --env-file .env hpi-chatbot-frontend```

---

## 🧪 Testing

To test the app locally:

1. Run the app without Docker:  
   `streamlit run app/main.py`

2. Ensure you have Python and the required dependencies installed:  
   `pip install -r requirements.txt`

---

## 🏗️ Building for Production

For a production-ready deployment:

1. Build the Docker image:  
   `docker build -t hpi-chatbot-frontend .`

2. Push the image to a container registry (e.g., Docker Hub, AWS ECR):  
   `docker tag hpi-chatbot-frontend <your-registry>/hpi-chatbot-frontend`  
   `docker push <your-registry>/hpi-chatbot-frontend`

3. Deploy the image on a platform like **Kubernetes**, **AWS ECS**, or **Azure Container Apps**.

---

## 🛠️ Technologies Used

- **Streamlit**: For creating the frontend.  
- **Docker**: For containerization.  
- **Python**: Backend logic and integrations.  
- **Docker Compose**: Simplified multi-container management.  

---

## 🤝 Contributing

We welcome contributions! Follow these steps to get started:

1. Fork the repository.  
2. Clone your fork:  
   `git clone https://github.com/your-username/hpi_chatbot_frontend.git`  
3. Create a new branch for your feature:  
   `git checkout -b feature/your-feature-name`  
4. Commit your changes:  
   `git commit -m "Add your message here"`  
5. Push your branch and create a pull request.  

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 📧 Support

For support, open an issue in the [GitHub repository](https://github.com/nestauk/hpi_chatbot_frontend/issues).

