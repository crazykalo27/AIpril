# API Reference

This API reference is organized by resource type. Each resource type has one or more data representations and one or more methods.

## Resource types

1. [Acl](https://developers.google.com/workspace/calendar/api/v3/reference#Acl)
2. [CalendarList](https://developers.google.com/workspace/calendar/api/v3/reference#CalendarList)
3. [Calendars](https://developers.google.com/workspace/calendar/api/v3/reference#Calendars)
4. [Channels](https://developers.google.com/workspace/calendar/api/v3/reference#Channels)
5. [Colors](https://developers.google.com/workspace/calendar/api/v3/reference#Colors)
6. [Events](https://developers.google.com/workspace/calendar/api/v3/reference#Events)
7. [Freebusy](https://developers.google.com/workspace/calendar/api/v3/reference#Freebusy)
8. [Settings](https://developers.google.com/workspace/calendar/api/v3/reference#Settings)

## Acl

For Acl Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/acl#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [delete](https://developers.google.com/workspace/calendar/api/v3/reference/acl/delete) | `DELETE /calendars/calendarId/acl/ruleId` | Deletes an access control rule. |
| [get](https://developers.google.com/workspace/calendar/api/v3/reference/acl/get) | `GET /calendars/calendarId/acl/ruleId` | Returns an access control rule. |
| [insert](https://developers.google.com/workspace/calendar/api/v3/reference/acl/insert) | `POST /calendars/calendarId/acl` | Creates an access control rule. |
| [list](https://developers.google.com/workspace/calendar/api/v3/reference/acl/list) | `GET /calendars/calendarId/acl` | Returns the rules in the access control list for the calendar. |
| [patch](https://developers.google.com/workspace/calendar/api/v3/reference/acl/patch) | `PATCH /calendars/calendarId/acl/ruleId` | Updates an access control rule. This method supports patch semantics. Note that each patch request consumes three quota units; prefer using a `get` followed by an `update`. The field values you specify replace the existing values. Fields that you don't specify in the request remain unchanged. Array fields, if specified, overwrite the existing arrays; this discards any previous array elements. |
| [update](https://developers.google.com/workspace/calendar/api/v3/reference/acl/update) | `PUT /calendars/calendarId/acl/ruleId` | Updates an access control rule. |
| [watch](https://developers.google.com/workspace/calendar/api/v3/reference/acl/watch) | `POST /calendars/calendarId/acl/watch` | Watch for changes to ACL resources. |

## CalendarList

For CalendarList Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [delete](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/delete) | `DELETE /users/me/calendarList/calendarId` | Removes a calendar from the user's calendar list. |
| [get](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/get) | `GET /users/me/calendarList/calendarId` | Returns a calendar from the user's calendar list. |
| [insert](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/insert) | `POST /users/me/calendarList` | Inserts an existing calendar into the user's calendar list. |
| [list](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/list) | `GET /users/me/calendarList` | Returns the calendars on the user's calendar list. |
| [patch](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/patch) | `PATCH /users/me/calendarList/calendarId` | Updates an existing calendar on the user's calendar list. This method supports patch semantics. Note that each patch request consumes three quota units; prefer using a `get` followed by an `update`. The field values you specify replace the existing values. Fields that you don't specify in the request remain unchanged. Array fields, if specified, overwrite the existing arrays; this discards any previous array elements. |
| [update](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/update) | `PUT /users/me/calendarList/calendarId` | Updates an existing calendar on the user's calendar list. |
| [watch](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/watch) | `POST /users/me/calendarList/watch` | Watch for changes to CalendarList resources. |

## Calendars

For Calendars Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/calendars#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [clear](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/clear) | `POST /calendars/calendarId/clear` | Clears a primary calendar. This operation deletes all events associated with the primary calendar of an account. |
| [delete](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/delete) | `DELETE /calendars/calendarId` | Deletes a secondary calendar. Use calendars.clear for clearing all events on primary calendars. |
| [get](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/get) | `GET /calendars/calendarId` | Returns metadata for a calendar. |
| [insert](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/insert) | `POST /calendars` | Creates a secondary calendar. The authenticated user for the request is made the data owner of the new calendar. <br /> **Note:** We recommend to authenticate as the intended data owner of the calendar. You can use [domain-wide delegation of authority](https://developers.google.com/workspace/cloud-search/docs/guides/delegation) to allow applications to act on behalf of a specific user. Don't use a service account for authentication. If you use a service account for authentication, the service account is the data owner, which can lead to unexpected behavior. For example, if a service account is the data owner, data ownership cannot be transferred. <br /> |
| [patch](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/patch) | `PATCH /calendars/calendarId` | Updates metadata for a calendar. This method supports patch semantics. Note that each patch request consumes three quota units; prefer using a `get` followed by an `update`. The field values you specify replace the existing values. Fields that you don't specify in the request remain unchanged. Array fields, if specified, overwrite the existing arrays; this discards any previous array elements. |
| [update](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/update) | `PUT /calendars/calendarId` | Updates metadata for a calendar. |

## Channels

For Channels Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/channels#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [stop](https://developers.google.com/workspace/calendar/api/v3/reference/channels/stop) | `POST /channels/stop` | Stop watching resources through this channel. |

## Colors

For Colors Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/colors#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [get](https://developers.google.com/workspace/calendar/api/v3/reference/colors/get) | `GET /colors` | Returns the color definitions for calendars and events. |

## Events

For Events Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/events#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [delete](https://developers.google.com/workspace/calendar/api/v3/reference/events/delete) | `DELETE /calendars/calendarId/events/eventId` | Deletes an event. |
| [get](https://developers.google.com/workspace/calendar/api/v3/reference/events/get) | `GET /calendars/calendarId/events/eventId` | Returns an event based on its Google Calendar ID. To retrieve an event using its iCalendar ID, call the [events.list method using the `iCalUID` parameter](https://developers.google.com/workspace/calendar/api/v3/reference/events/list#iCalUID). |
| [import](https://developers.google.com/workspace/calendar/api/v3/reference/events/import) | `POST /calendars/calendarId/events/import` | Imports an event. This operation is used to add a private copy of an existing event to a calendar. Only events with an `eventType` of `default` may be imported. **Deprecated behavior:** If a non-`default` event is imported, its type will be changed to `default` and any event-type-specific properties it may have will be dropped. |
| [insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert) | `POST /calendars/calendarId/events` | Creates an event. |
| [instances](https://developers.google.com/workspace/calendar/api/v3/reference/events/instances) | `GET /calendars/calendarId/events/eventId/instances` | Returns instances of the specified recurring event. |
| [list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list) | `GET /calendars/calendarId/events` | Returns events on the specified calendar. |
| [move](https://developers.google.com/workspace/calendar/api/v3/reference/events/move) | `POST /calendars/calendarId/events/eventId/move` | Moves an event to another calendar, i.e. changes an event's organizer. Note that only `default` events can be moved; `birthday`, `focusTime`, `fromGmail`, `outOfOffice` and `workingLocation` events cannot be moved. <br /> **Required query parameters:** `destination` |
| [patch](https://developers.google.com/workspace/calendar/api/v3/reference/events/patch) | `PATCH /calendars/calendarId/events/eventId` | Updates an event. This method supports patch semantics. Note that each patch request consumes three quota units; prefer using a `get` followed by an `update`. The field values you specify replace the existing values. Fields that you don't specify in the request remain unchanged. Array fields, if specified, overwrite the existing arrays; this discards any previous array elements. |
| [quickAdd](https://developers.google.com/workspace/calendar/api/v3/reference/events/quickAdd) | `POST /calendars/calendarId/events/quickAdd` | Creates an event based on a simple text string. <br /> **Required query parameters:** `text` |
| [update](https://developers.google.com/workspace/calendar/api/v3/reference/events/update) | `PUT /calendars/calendarId/events/eventId` | Updates an event. This method does not support patch semantics and always updates the entire event resource. To do a partial update, perform a `get` followed by an `update` using etags to ensure atomicity. |
| [watch](https://developers.google.com/workspace/calendar/api/v3/reference/events/watch) | `POST /calendars/calendarId/events/watch` | Watch for changes to Events resources. |

## Freebusy

For Freebusy Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [query](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query) | `POST /freeBusy` | Returns free/busy information for a set of calendars. |

## Settings

For Settings Resource details, see the [resource representation](https://developers.google.com/workspace/calendar/api/v3/reference/settings#resource) page.

| Method | HTTP request | Description |
|---|---|---|
| URIs relative to https://www.googleapis.com/calendar/v3, unless otherwise noted |||
| [get](https://developers.google.com/workspace/calendar/api/v3/reference/settings/get) | `GET /users/me/settings/setting` | Returns a single user setting. |
| [list](https://developers.google.com/workspace/calendar/api/v3/reference/settings/list) | `GET /users/me/settings` | Returns all user settings for the authenticated user. |
| [watch](https://developers.google.com/workspace/calendar/api/v3/reference/settings/watch) | `POST /users/me/settings/watch` | Watch for changes to Settings resources. |