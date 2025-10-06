#include <iostream>
#include <cmath>
#include <chrono>
#include <thread>
#include <string>
#include <vector>
#include <map>
#include <fstream>
using namespace std;

int main(int argc, char** argv){
    if(argc < 3){
        cout << "Usage: ./task_worker <task_name> <work_seconds>\n";
        return 1;
    }
    string name = argv[1];
    int secs = stoi(argv[2]);

    cout << "[task " << name << "] started, simulating " << secs << "s busy-work\n";
    auto start = chrono::high_resolution_clock::now();
    volatile double sink = 0.0;
    // Busy loop to simulate CPU use for approx `secs` seconds.
    while(true){
        for(int i=0;i<10000;i++){
            sink += sqrt((i+1.0) * 3.14159);
        }
        auto now = chrono::high_resolution_clock::now();
        double elapsed = chrono::duration<double>(now - start).count();
        if(elapsed >= secs) break;
    }
    cout << "[task " << name << "] finished (simulated).\\n";
    // Prevent optimizer removing sink
    if(sink < 0) cout << sink;
    return 0;
}
