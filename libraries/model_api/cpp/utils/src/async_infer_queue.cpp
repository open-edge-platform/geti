/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "utils/async_infer_queue.hpp"

AsyncInferQueue::AsyncInferQueue(ov::CompiledModel& model, size_t jobs) {
    if (jobs == 0) {
        jobs = static_cast<size_t>(model.get_property(ov::optimal_number_of_infer_requests));
    }

    m_requests.reserve(jobs);
    m_user_ids.reserve(jobs);

    for (size_t handle = 0; handle < jobs; handle++) {
        // Create new "empty" InferRequest without pre-defined callback and
        // copy Inputs and Outputs from ov::CompiledModel
        m_requests.emplace_back(model.create_infer_request());
        m_user_ids.push_back(nullptr);
        m_idle_handles.push(handle);
    }

    set_default_callbacks();
}

bool AsyncInferQueue::is_ready() {
    // acquire the mutex to access m_errors and m_idle_handles
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_errors.size() > 0)
        throw m_errors.front();
    return !(m_idle_handles.empty());
}

size_t AsyncInferQueue::get_idle_request_id() {
    // Wait for any request to complete and return its id
    // acquire the mutex to access m_errors and m_idle_handles
    std::unique_lock<std::mutex> lock(m_mutex);
    m_cv.wait(lock, [this] {
        return !(m_idle_handles.empty());
    });
    size_t idle_handle = m_idle_handles.front();
    // wait for request to make sure it returned from callback
    m_requests[idle_handle].wait();
    if (m_errors.size() > 0)
        throw m_errors.front();
    return idle_handle;
}

void AsyncInferQueue::wait_all() {
    // Wait for all request to complete
    for (auto&& request : m_requests) {
        request.wait();
    }
    // acquire the mutex to access m_errors
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_errors.size() > 0)
        throw m_errors.front();
}

void AsyncInferQueue::set_default_callbacks() {
    for (size_t handle = 0; handle < m_requests.size(); handle++) {
        m_requests[handle].set_callback([this, handle](std::exception_ptr exception_ptr) {
            {
                // acquire the mutex to access m_idle_handles
                std::lock_guard<std::mutex> lock(m_mutex);
                // Add idle handle to queue
                m_idle_handles.push(handle);
            }
            // Notify locks in getIdleRequestId()
            m_cv.notify_one();

            try {
                if (exception_ptr) {
                    std::rethrow_exception(exception_ptr);
                }
            } catch (const std::exception& ex) {
                std::lock_guard<std::mutex> lock(m_mutex);
                m_errors.push(std::make_shared<std::exception>(ex));
            }
        });
    }
}

void AsyncInferQueue::set_custom_callbacks(
    std::function<void(ov::InferRequest, std::shared_ptr<ov::AnyMap>)> f_callback) {
    for (size_t handle = 0; handle < m_requests.size(); handle++) {
        m_requests[handle].set_callback([this, f_callback, handle](std::exception_ptr exception_ptr) {
            if (exception_ptr == nullptr) {
                try {
                    f_callback(m_requests[handle], m_user_ids[handle]);
                } catch (std::exception& ex) {
                    // acquire the mutex to access m_errors
                    std::lock_guard<std::mutex> lock(m_mutex);
                    m_errors.push(std::make_shared<std::exception>(ex));
                }
            } else {
                try {
                    std::rethrow_exception(exception_ptr);
                } catch (const std::exception& ex) {
                    std::lock_guard<std::mutex> lock(m_mutex);
                    m_errors.push(std::make_shared<std::exception>(ex));
                }
            }

            {
                // acquire the mutex to access m_idle_handles
                std::lock_guard<std::mutex> lock(m_mutex);
                // Add idle handle to queue
                m_idle_handles.push(handle);
            }
            // Notify locks in getIdleRequestId()
            m_cv.notify_one();
        });
    }
}

size_t AsyncInferQueue::size() const {
    return m_requests.size();
}

void AsyncInferQueue::start_async(const ov::Tensor& input, std::shared_ptr<ov::AnyMap> userdata) {
    // getIdleRequestId function has an intention to block InferQueue
    // until there is at least one idle (free to use) InferRequest
    auto handle = get_idle_request_id();
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_idle_handles.pop();
    }
    m_user_ids[handle] = userdata;
    m_requests[handle].set_input_tensor(input);
    m_requests[handle].start_async();
}

void AsyncInferQueue::start_async(const std::map<std::string, ov::Tensor>& input,
                                  std::shared_ptr<ov::AnyMap> userdata) {
    // getIdleRequestId function has an intention to block InferQueue
    // until there is at least one idle (free to use) InferRequest
    auto handle = get_idle_request_id();
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_idle_handles.pop();
    }
    m_user_ids[handle] = userdata;
    for (const auto& item : input) {
        m_requests[handle].set_tensor(item.first, item.second);
    }
    m_requests[handle].start_async();
}

ov::InferRequest AsyncInferQueue::operator[](size_t i) {
    return m_requests[i];
}
