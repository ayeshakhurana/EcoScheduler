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
    if (bp != string::npos) battery = stod(content.substr(bp + 17));

    // --- Load profiles ---
    ifstream pfile("profiles.json");
    string prof((istreambuf_iterator<char>(pfile)), istreambuf_iterator<char>());
    cout << "Profiles: " << prof << "\n";

    // --- Load tasks ---
    vector<Task> tasks = loadTasks("tasks.txt");
    cout << "Loaded " << tasks.size() << " tasks.\n";

    ofstream log("log.txt", ios::app);
    ofstream csv("logs.csv", ios::app);
    csv << "\"timestamp\",task,action,label,energy,battery,on_ac\n";

    for (auto& t : tasks) {
        string label = "medium";
        if (prof.find(t.name) != string::npos) {
            if (prof.find("\"" + t.name + "\": \"low\"") != string::npos) label = "low";
            else if (prof.find("\"" + t.name + "\": \"high\"") != string::npos) label = "high";
        }

        double energy = (label == "low" ? 0.5 : label == "medium" ? 1.0 : 2.0) * t.seconds;

        if (!on_ac && battery < 30 && label == "high") {
            cout << "⚠️  Battery low and task " << t.name << " is high energy. Defer? (y/n): ";
            char ans;
            cin >> ans;
            auto now = chrono::system_clock::now();
            time_t now_c = chrono::system_clock::to_time_t(now);
            string timeStr = trim(std::string(std::ctime(&now_c)));
            csv << "\"" << timeStr << "\"," << t.name << ",deferred," << label << "," << energy << "," << battery << "," << (on_ac ? 1 : 0) << "\n";
            if (ans == 'y' || ans == 'Y') {
                cout << "Running anyway...\n";
            } else {
                cout << "Deferred " << t.name << " due to low battery.\n";
                continue;
            }
        }

        cout << "🔹 Executing " << t.name << " (" << t.seconds << "s, " << label << ")\n";
        auto start = chrono::high_resolution_clock::now();
        string cmd = "./task_worker CPU " + to_string(t.seconds);
        system(cmd.c_str());
        auto end = chrono::high_resolution_clock::now();
        double dur = chrono::duration<double>(end - start).count();

        auto now = chrono::system_clock::now();
        time_t now_c = chrono::system_clock::to_time_t(now);
        string timeStr = trim(std::string(std::ctime(&now_c)));

        log << t.name << ": executed (" << label << ", " << energy << ")\n";
        csv << "\"" << timeStr << "\"," << t.name << ",executed," << label << "," << energy << "," << battery << "," << (on_ac ? 1 : 0) << "\n";
    }

    csv.close();
    log.close();
    cout << "✅ Run complete — logs.txt and logs.csv written.\n";
    return 0;
}
