use ccmonitor::{git_utils, claude_logs, SessionEvent, SessionTimeline};
use chrono::{DateTime, Local, TimeZone};
use std::path::PathBuf;
use tempfile::tempdir;
use std::fs;

#[test]
fn test_git_repository_name_extraction() {
    // Test various URL formats
    assert_eq!(git_utils::get_repository_name("/nonexistent/path"), None);
}

#[test]
fn test_session_event_creation() {
    let timestamp = Local.with_ymd_and_hms(2023, 12, 25, 10, 0, 0).unwrap();
    
    let event = SessionEvent {
        timestamp,
        session_id: "test-session".to_string(),
        directory: "/tmp/test".to_string(),
        message_type: "user".to_string(),
        content_preview: "Test message".to_string(),
        uuid: "test-uuid".to_string(),
        input_tokens: 10,
        output_tokens: 20,
    };

    assert_eq!(event.session_id, "test-session");
    assert_eq!(event.input_tokens, 10);
    assert_eq!(event.output_tokens, 20);
}

#[test]
fn test_active_duration_calculation() {
    let base_time = Local.with_ymd_and_hms(2023, 12, 25, 10, 0, 0).unwrap();
    
    // Test with events 30 seconds apart (should be counted)
    let events = vec![
        SessionEvent {
            timestamp: base_time,
            session_id: "test".to_string(),
            directory: "/tmp".to_string(),
            message_type: "user".to_string(),
            content_preview: "msg1".to_string(),
            uuid: "uuid1".to_string(),
            input_tokens: 0,
            output_tokens: 0,
        },
        SessionEvent {
            timestamp: base_time + chrono::Duration::seconds(30),
            session_id: "test".to_string(),
            directory: "/tmp".to_string(),
            message_type: "assistant".to_string(),
            content_preview: "msg2".to_string(),
            uuid: "uuid2".to_string(),
            input_tokens: 10,
            output_tokens: 20,
        },
    ];

    let duration = claude_logs::calculate_active_duration(&events);
    assert_eq!(duration, 0); // 30 seconds is less than 1 minute, so 0 minutes active

    // Test with single event (should be 5 minutes minimum)
    let single_event = vec![events[0].clone()];
    let single_duration = claude_logs::calculate_active_duration(&single_event);
    assert_eq!(single_duration, 5);
}

#[test]
fn test_token_calculation() {
    let events = vec![
        SessionEvent {
            timestamp: Local::now(),
            session_id: "test".to_string(),
            directory: "/tmp".to_string(),
            message_type: "user".to_string(),
            content_preview: "user message".to_string(),
            uuid: "uuid1".to_string(),
            input_tokens: 0,
            output_tokens: 0,
        },
        SessionEvent {
            timestamp: Local::now(),
            session_id: "test".to_string(),
            directory: "/tmp".to_string(),
            message_type: "assistant".to_string(),
            content_preview: "assistant message".to_string(),
            uuid: "uuid2".to_string(),
            input_tokens: 100,
            output_tokens: 50,
        },
        SessionEvent {
            timestamp: Local::now(),
            session_id: "test".to_string(),
            directory: "/tmp".to_string(),
            message_type: "assistant".to_string(),
            content_preview: "another assistant message".to_string(),
            uuid: "uuid3".to_string(),
            input_tokens: 75,
            output_tokens: 25,
        },
    ];

    let (input_total, output_total) = claude_logs::calculate_token_totals(&events);
    assert_eq!(input_total, 175);  // 0 + 100 + 75
    assert_eq!(output_total, 75);  // 0 + 50 + 25
}

#[test]
fn test_parse_empty_jsonl() {
    // Create a temporary empty file
    let dir = tempdir().unwrap();
    let file_path = dir.path().join("empty.jsonl");
    fs::write(&file_path, "").unwrap();

    let result = claude_logs::parse_jsonl_file(&file_path);
    assert!(result.is_ok());
    assert!(result.unwrap().is_empty());
}