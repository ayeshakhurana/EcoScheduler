#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <thread>
#include <cstdlib>
#include <chrono>
#include <string>
#include <ctime>
#include <algorithm>
using namespace std;

struct Task {
    string name;
    int seconds;
};

vector<Task> loadTasks(const string& filename) {
    vector<Task> tasks;
    ifstream file(filename);
    string line;
    while (getline(file, line)) {
        if (line.empty() || line[0] == '#') continue;
        stringstream ss(line);
        string name, secStr;
        getline(ss, name, ',');
        getline(ss, secStr, ',');
        tasks.push_back({name, stoi(secStr)});
    }
    return tasks;
}

string trim(const string& s) {
    string out = s;
    out.erase(remove(out.begin(), out.end(), '\n'), out.end());
    out.erase(remove(out.begin(), out.end(), '\r'), out.end());
    return out;
}

int priorityFromLabel(const string& label) {
    if (label == "high") return 3;
    if (label == "medium") return 2;
    return 1;
}

int main() {
    cout << "🌿 EcoScheduler v3 — CSV Logging Enabled\n";

    // --- Load monitor info ---
    double battery = 100;
    bool on_ac = true;
    ifstream mon("monitor.txt");
    string content((istreambuf_iterator<char>(mon)), istreambuf_iterator<char>());
    cout << "System info: " << content << "\n";
    if (content.find("False") != string::npos || content.find("false") != string::npos) on_ac = false;
    size_t bp = content.find("battery_percent");
    if (bp != string::npos) {
        size_t comma = content.find(',', bp);
        string val = content.substr(bp + 16, comma - (bp + 16));
        battery = stod(trim(val));
    }

    // --- Load profiles ---
    ifstream pfile("profiles.json");
    string prof((istreambuf_iterator<char>(pfile)), istreambuf_iterator<char>());
    cout << "Profiles: " << prof << "\n";

    // --- Load tasks ---
    vector<Task> tasks = loadTasks("tasks.txt");

    // --- Determine task labels and sort by priority ---
    sort(tasks.begin(), tasks.end(), [&](const Task& a, const Task& b){
        string labelA = "medium", labelB = "medium";
        if (prof.find("\"" + a.name + "\": \"low\"") != string::npos) labelA = "low";
        else if (prof.find("\"" + a.name + "\": \"high\"") != string::npos) labelA = "high";
        if (prof.find("\"" + b.name + "\": \"low\"") != string::npos) labelB = "low";
        else if (prof.find("\"" + b.name + "\": \"high\"") != string::npos) labelB = "high";
        return priorityFromLabel(labelA) > priorityFromLabel(labelB);
    });

    cout << "Loaded " << tasks.size() << " tasks.\n";

    ofstream log("log.txt", ios::app);
    ofstream csv("logs.csv", ios::app);
    csv << "\"timestamp\",task,action,label,energy,battery,on_ac\n";

    for (auto& t : tasks) {
    string label = "medium";
    if (prof.find("\"" + t.name + "\": \"low\"") != string::npos) label = "low";
    else if (prof.find("\"" + t.name + "\": \"high\"") != string::npos) label = "high";

    double energy = (label == "low" ? 0.5 : label == "medium" ? 1.0 : 2.0) * t.seconds;

    bool deferred = false;
    // --- Autonomous defer ---
    if (!on_ac && battery < 30 && label == "high") {
        deferred = true;
        cout << "⚠️  Battery low. Automatically deferring high-energy task: " << t.name << "\n";
    }

    auto now = chrono::system_clock::now();
    time_t now_c = chrono::system_clock::to_time_t(now);
    string timeStr = trim(std::string(std::ctime(&now_c)));

    if (deferred) {
        csv << "\"" << timeStr << "\"," << t.name << ",deferred," << label << "," << energy << "," << battery << "," << (on_ac ? 1 : 0) << "\n";
        log << t.name << ": deferred (" << label << ", " << energy << ")\n";
        continue; // skip execution
    }

    // Execute task
    cout << "🔹 Executing " << t.name << " (" << t.seconds << "s, " << label << ")\n";
    string cmd = "./task_worker CPU " + to_string(t.seconds);
    system(cmd.c_str());

    log << t.name << ": executed (" << label << ", " << energy << ")\n";
    csv << "\"" << timeStr << "\"," << t.name << ",executed," << label << "," << energy << "," << battery << "," << (on_ac ? 1 : 0) << "\n";
}


    csv.close();
    log.close();
    cout << "✅ Run complete — logs.txt and logs.csv written.\n";
    return 0;
}
