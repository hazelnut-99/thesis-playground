#include <iostream>
#include <chrono>
#include <ctime>
#include <dlfcn.h>

// Define function pointer for set_mock_time
typedef void (*set_mock_time_t)(time_t, long);

int main() {
    // Load the shared library
    void* handle = dlopen("./libmock_time.so", RTLD_LAZY);
    if (!handle) {
        std::cerr << "Failed to load libmock_time.so\n";
        return 1;
    }

    // Get the function pointer for set_mock_time
    set_mock_time_t set_mock_time = (set_mock_time_t)dlsym(handle, "set_mock_time");
    if (!set_mock_time) {
        std::cerr << "Failed to find function set_mock_time()\n";
        return 1;
    }

    // Set mock time to a specific timestamp (e.g., 1700000000 seconds since epoch)
    set_mock_time(1700000000, 0);

    // Retrieve time using std::chrono::system_clock::now()
    auto now = std::chrono::system_clock::now();
    std::time_t now_c = std::chrono::system_clock::to_time_t(now);

    // Print the retrieved time
    std::cout << "Mock time set to: " << 1700000000 << " (Epoch seconds)\n";
    std::cout << "std::chrono::system_clock::now() retrieved: " << now_c << " (Epoch seconds)\n";

    // Verify if the times match
    if (now_c == 1700000000) {
        std::cout << "✅ Test Passed: std::chrono reflects the mock time!\n";
    } else {
        std::cout << "❌ Test Failed: std::chrono does not match the mock time!\n";
    }

    // Retrieve time using std::time(nullptr)
    std::time_t time_now = std::time(nullptr);

    // Print the retrieved time
    std::cout << "std::time(nullptr) retrieved: " << time_now << " (Epoch seconds)\n";

    // Verify if the times match
    if (time_now == 1700000000) {
        std::cout << "✅ Test Passed: std::time reflects the mock time!\n";
    } else {
        std::cout << "❌ Test Failed: std::time does not match the mock time!\n";
    }

    // Close the shared library
    dlclose(handle);
    return 0;
}
