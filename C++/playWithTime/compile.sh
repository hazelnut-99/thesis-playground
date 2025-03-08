g++ -shared -fPIC -o libmock_time.so libmock_time.cpp -ldl
g++ -o test_mock_time test_mock_time.cpp