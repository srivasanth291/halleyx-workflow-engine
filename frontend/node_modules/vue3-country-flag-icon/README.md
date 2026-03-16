# vue3-country-flag-icon

Country flag component for Vue 3. Supports SSR apps.

Forked from <https://github.com/dzangolab/vue-country-flag-icon>

## Usage

Add the package to your app via npm:

``` bash
npm install vue3-country-flag-icon
```

or yarn:

``` bash
yarn add vue3-country-flag-icon
```

### Add CountryFlag globally

``` javascript
# main.js

import { createApp } from 'vue'
import App from './App.vue'
import CountryFlag from 'vue3-country-flag-icon'
import 'vue3-country-flag-icon/dist/CountryFlag.css' // import stylesheet

const app = createApp(App)
app.component('country-flag', CountryFlag)
```

### Add CountryFlag inside a component

```javascript
# MyComponent.vue
<template>
  <CountryFlag iso="GB" mode="squared" />
  <CountryFlag iso="GB" mode="rounded" />
</template>

<script>
  import CountryFlag from 'vue3-country-flag-icon'
  import 'vue3-country-flag-icon/dist/CountryFlag.css' // import stylesheet

  export default {
    components: {
      CountryFlag
    }
  }
</script>
```

## Props

### `iso`

country ISO code (alpha-2 code).

This setting is **required**.

### `title`

title for the country flag.

### `mode`

Determines the behavior of the country flag. This component support 2 modes `rounded` and `squared`.

This setting is **required**.

## SCSS

Instead of importing the css file in component or main.js, you can also import scss file into your app scss file.

```javascript
@import '~vue3-country-flag-icon/src/assets/scss/country-flag.scss';
```
