use std::process::{Command, Child, Stdio};
use std::sync::Mutex;
use std::thread;

// Global reference to the Python backend process
static BACKEND_PROCESS: Mutex<Option<Child>> = Mutex::new(None);


// API Commands
#[tauri::command]
async fn api_get_tasks() -> Result<String, String> {
    println!("🦀 Rust: Getting tasks from API");
    
    match std::process::Command::new("curl")
        .args(["-s", "http://localhost:5001/api/tasks"])
        .output()
    {
        Ok(output) => {
            if output.status.success() {
                let response = String::from_utf8_lossy(&output.stdout);
                println!("✅ Got tasks: {}", response.len());
                Ok(response.to_string())
            } else {
                let error = String::from_utf8_lossy(&output.stderr);
                Err(format!("API request failed: {}", error))
            }
        }
        Err(e) => Err(format!("Failed to call API: {}", e)),
    }
}

#[tauri::command]
async fn api_create_task(title: String, description: String, project: Option<String>, categories: Option<String>) -> Result<String, String> {
    println!("🦀 Rust: Creating task - title: {}, desc: {}, project: {:?}, categories: {:?}", title, description, project, categories);
    
    let mut json_body = format!(r#"{{"title": "{}", "description": "{}""#, 
                               title.replace("\"", "\\\""), 
                               description.replace("\"", "\\\""));
    
    if let Some(proj) = project {
        json_body.push_str(&format!(r#", "project": "{}""#, proj.replace("\"", "\\\"")));
    }
    
    if let Some(cats) = categories {
        // Parse categories from comma-separated string to array
        let categories_array: Vec<&str> = cats.split(',').map(|s| s.trim()).collect();
        let categories_json = serde_json::to_string(&categories_array).unwrap_or_else(|_| "[]".to_string());
        json_body.push_str(&format!(r#", "categories": {}"#, categories_json));
    } else {
        json_body.push_str(r#", "categories": []"#);
    }
    
    json_body.push('}');
    
    match std::process::Command::new("curl")
        .args([
            "-X", "POST",
            "http://localhost:5001/api/tasks",
            "-H", "Content-Type: application/json",
            "-d", &json_body,
            "-s"
        ])
        .output()
    {
        Ok(output) => {
            if output.status.success() {
                let response = String::from_utf8_lossy(&output.stdout);
                println!("✅ Task created: {}", response);
                Ok(response.to_string())
            } else {
                let error = String::from_utf8_lossy(&output.stderr);
                Err(format!("Create task failed: {}", error))
            }
        }
        Err(e) => Err(format!("Failed to create task: {}", e)),
    }
}

#[tauri::command]
async fn api_update_task_status(task_id: u32, status: String) -> Result<String, String> {
    println!("🦀 Rust: Updating task status - task_id: {}, status: {}", task_id, status);
    
    let json_body = format!(r#"{{"status": "{}"}}"#, status.replace("\"", "\\\""));
    
    match std::process::Command::new("curl")
        .args([
            "-X", "PATCH",
            &format!("http://localhost:5001/api/tasks/{}/status", task_id),
            "-H", "Content-Type: application/json",
            "-d", &json_body,
            "-s"
        ])
        .output()
    {
        Ok(output) => {
            if output.status.success() {
                let response = String::from_utf8_lossy(&output.stdout);
                println!("✅ Task status updated: {}", response);
                Ok(response.to_string())
            } else {
                let error = String::from_utf8_lossy(&output.stderr);
                Err(format!("Update task status failed: {}", error))
            }
        }
        Err(e) => Err(format!("Failed to update task status: {}", e)),
    }
}

#[tauri::command]
fn check_backend_status() -> Result<String, String> {
    // Try to make a request to the Python backend using curl
    match std::process::Command::new("curl")
        .args(["-s", "-f", "http://localhost:5001/api/tasks"])
        .output()
    {
        Ok(output) => {
            if output.status.success() {
                Ok("Backend is running".to_string())
            } else {
                Err("Backend not responding".to_string())
            }
        }
        Err(_) => Err("Could not check backend status".to_string()),
    }
}

#[tauri::command]
fn start_python_backend() -> Result<String, String> {
    println!("🚀 Starting Python backend...");
    
    // Get the parent directory (where your Python app.py is located)
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("Failed to get executable path: {}", e))?;
    
    let parent_dir = exe_path.parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .ok_or("Could not determine parent directory")?;
    
    println!("🔍 Looking for Python backend in: {:?}", parent_dir);
    
    // Try different possible locations for the Python backend
    let possible_paths = vec![
        parent_dir.join("app.py"),
        parent_dir.parent().unwrap_or(parent_dir).join("app.py"),
        std::path::PathBuf::from("../app.py"),
        std::path::PathBuf::from("../../app.py"),
    ];
    
    let mut backend_path = None;
    for path in possible_paths {
        if path.exists() {
            backend_path = Some(path);
            break;
        }
    }
    
    let backend_path = backend_path.ok_or("Could not find app.py. Please ensure it's in the parent directory.")?;
    
    println!("✅ Found Python backend at: {:?}", backend_path);
    
    // Start the Python backend process with correct working directory
    let backend_dir = backend_path.parent().unwrap_or_else(|| std::path::Path::new("."));
    let child = Command::new("python3")
        .arg(backend_path.file_name().unwrap())
        .current_dir(backend_dir)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start Python backend: {}", e))?;
    
    // Store the process handle globally so we can kill it later
    *BACKEND_PROCESS.lock().unwrap() = Some(child);
    
    println!("🎉 Python backend started successfully!");
    Ok("Python backend started".to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_http::init())
        .invoke_handler(tauri::generate_handler![
            check_backend_status,
            start_python_backend,
            api_get_tasks,
            api_create_task,
            api_update_task_status
        ])
        .setup(|_app| {
            // Start the Python backend when the app launches in a separate thread
            thread::spawn(move || {
                // Wait a moment for the app to fully initialize
                thread::sleep(std::time::Duration::from_millis(500));
                
                match start_python_backend() {
                    Ok(msg) => println!("✅ {}", msg),
                    Err(err) => eprintln!("❌ Failed to start backend: {}", err),
                }
                
                // Wait longer and retry backend health check multiple times
                for i in 1..=10 {
                    thread::sleep(std::time::Duration::from_millis(1000));
                    match check_backend_status() {
                        Ok(msg) => {
                            println!("✅ Backend ready after {}s: {}", i, msg);
                            break;
                        },
                        Err(err) => {
                            if i == 10 {
                                eprintln!("❌ Backend failed to start after 10s: {}", err);
                            } else {
                                println!("⏳ Waiting for backend... ({}s)", i);
                            }
                        }
                    }
                }
            });
            
            Ok(())
        })
        .on_window_event(|_window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                // Clean up the Python backend process when the window closes
                if let Ok(mut process) = BACKEND_PROCESS.lock() {
                    if let Some(mut child) = process.take() {
                        let _ = child.kill();
                        println!("🛑 Python backend process terminated");
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
