/**
 * PlatformIO unit test entry point.
 *
 * Run with: pio test
 *
 * These tests run on native platform or on-device.
 */

#include <Arduino.h>
#include <unity.h>

// Include modules to test
#include "services/calendar/reclaim_detector.h"
#include "services/prompt/prompt_scheduler.h"

void test_reclaim_detected_in_summary() {
    ReclaimDetector detector("[reclaim]");
    CalendarEvent ev;
    ev.summary = "Focus time [reclaim]";
    ev.description = "";
    TEST_ASSERT_TRUE(detector.isReclaim(ev));
}

void test_reclaim_not_found() {
    ReclaimDetector detector("[reclaim]");
    CalendarEvent ev;
    ev.summary = "Team standup";
    ev.description = "Daily sync";
    TEST_ASSERT_FALSE(detector.isReclaim(ev));
}

void test_reclaim_case_insensitive() {
    ReclaimDetector detector("[reclaim]");
    CalendarEvent ev;
    ev.summary = "[RECLAIM] Deep Work";
    TEST_ASSERT_TRUE(detector.isReclaim(ev));
}

void test_prompt_scheduler_initial_should_not_prompt() {
    PromptScheduler sched(60000);  // 60 seconds
    TEST_ASSERT_FALSE(sched.shouldPrompt());
}

void test_prompt_scheduler_suppressed() {
    PromptScheduler sched(0);  // 0ms = always due
    sched.suppress();
    TEST_ASSERT_FALSE(sched.shouldPrompt());
}

void setup() {
    delay(2000);
    UNITY_BEGIN();

    RUN_TEST(test_reclaim_detected_in_summary);
    RUN_TEST(test_reclaim_not_found);
    RUN_TEST(test_reclaim_case_insensitive);
    RUN_TEST(test_prompt_scheduler_initial_should_not_prompt);
    RUN_TEST(test_prompt_scheduler_suppressed);

    UNITY_END();
}

void loop() {}
